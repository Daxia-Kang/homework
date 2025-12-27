"""Game recorder - 录像记录器。

记录对局过程，支持导出和回放。
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from core.board import Stone

if TYPE_CHECKING:
    from player.base import PlayerAction


@dataclass
class MoveRecord:
    """单步记录。"""
    move_number: int
    player: str  # "BLACK" / "WHITE"
    action_type: str  # "move" / "pass" / "resign"
    position: Optional[tuple]  # (row, col) 或 None
    timestamp: float
    board_snapshot: Optional[List[List[str]]] = None  # 关键帧快照


@dataclass
class RecordMetadata:
    """录像元数据。"""
    game_type: str
    board_size: int
    black_player: str
    white_player: str
    start_time: str
    end_time: Optional[str] = None
    result: Optional[str] = None  # "BLACK_WIN" / "WHITE_WIN" / "DRAW"
    total_moves: int = 0
    user_id: Optional[str] = None


class GameRecorder:
    """录像记录器实现。
    
    功能：
    1. 记录每一步操作
    2. 定期保存棋盘快照（用于快速回放定位）
    3. 导出为可序列化格式
    """

    SNAPSHOT_INTERVAL = 10  # 每 10 步保存一次完整快照

    def __init__(
        self,
        game_type: str,
        board_size: int,
        black_player: str,
        white_player: str,
        user_id: Optional[str] = None
    ) -> None:
        """初始化录像记录器。
        
        Args:
            game_type: 游戏类型
            board_size: 棋盘大小
            black_player: 黑方玩家名
            white_player: 白方玩家名
            user_id: 关联的用户 ID
        """
        self._moves: List[MoveRecord] = []
        self._metadata = RecordMetadata(
            game_type=game_type,
            board_size=board_size,
            black_player=black_player,
            white_player=white_player,
            start_time=datetime.now().isoformat(),
            user_id=user_id
        )
        self._initial_board: Optional[List[List[str]]] = None

    def set_initial_board(self, board_snapshot: List[List[Stone]]) -> None:
        """设置初始棋盘状态。"""
        self._initial_board = [[cell.value for cell in row] for row in board_snapshot]

    def record_move(
        self,
        action: "PlayerAction",
        player: Stone,
        board_snapshot: List[List[Stone]],
        timestamp: Optional[float] = None
    ) -> None:
        """记录一步操作。
        
        Args:
            action: 玩家动作
            player: 执行动作的玩家
            board_snapshot: 当前棋盘状态
            timestamp: 时间戳（可选，默认当前时间）
        """
        move_num = len(self._moves) + 1
        ts = timestamp if timestamp is not None else time.time()

        # 增量存储：只在关键帧保存快照
        snapshot = None
        if move_num % self.SNAPSHOT_INTERVAL == 0:
            snapshot = [[cell.value for cell in row] for row in board_snapshot]

        position = None
        if action.row is not None and action.col is not None:
            position = (action.row, action.col)

        record = MoveRecord(
            move_number=move_num,
            player=player.name,
            action_type=action.action_type.value,
            position=position,
            timestamp=ts,
            board_snapshot=snapshot
        )
        self._moves.append(record)
        self._metadata.total_moves = move_num

    def finalize(self, result: str, final_board: List[List[Stone]]) -> None:
        """完成录像记录。
        
        Args:
            result: 游戏结果
            final_board: 最终棋盘状态
        """
        self._metadata.end_time = datetime.now().isoformat()
        self._metadata.result = result
        self._final_board = [[cell.value for cell in row] for row in final_board]

    def get_move_list(self) -> List[MoveRecord]:
        """获取所有步骤记录。"""
        return self._moves.copy()

    def get_metadata(self) -> RecordMetadata:
        """获取录像元数据。"""
        return self._metadata

    def export(self) -> Dict[str, Any]:
        """导出为可序列化的字典格式。"""
        return {
            "version": "2.0",
            "metadata": asdict(self._metadata),
            "initial_board": self._initial_board,
            "moves": [
                {
                    "move_number": m.move_number,
                    "player": m.player,
                    "action_type": m.action_type,
                    "position": list(m.position) if m.position else None,
                    "timestamp": m.timestamp,
                    "board_snapshot": m.board_snapshot
                }
                for m in self._moves
            ],
            "final_board": getattr(self, '_final_board', None)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameRecorder":
        """从字典数据恢复录像记录器。"""
        metadata = data.get("metadata", {})
        recorder = cls(
            game_type=metadata.get("game_type", "unknown"),
            board_size=metadata.get("board_size", 8),
            black_player=metadata.get("black_player", "Unknown"),
            white_player=metadata.get("white_player", "Unknown"),
            user_id=metadata.get("user_id")
        )
        recorder._metadata = RecordMetadata(**metadata)
        recorder._initial_board = data.get("initial_board")
        recorder._final_board = data.get("final_board")
        
        for m in data.get("moves", []):
            record = MoveRecord(
                move_number=m["move_number"],
                player=m["player"],
                action_type=m["action_type"],
                position=tuple(m["position"]) if m["position"] else None,
                timestamp=m["timestamp"],
                board_snapshot=m.get("board_snapshot")
            )
            recorder._moves.append(record)
        
        return recorder
