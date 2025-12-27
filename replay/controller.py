"""Replay controller - 回放控制器。

支持对局回放的前进、后退、跳转、自动播放功能。
设计模式：状态模式（简化版）- 管理播放状态。
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, List, Optional

from core.board import Board, Stone
from core.game import Game, GameFactory
from match.recorder import MoveRecord, RecordMetadata, GameRecorder


class ReplayController:
    """回放控制器实现。
    
    功能：
    1. 加载录像数据
    2. 前进/后退单步
    3. 跳转到指定步数
    4. 自动播放
    5. 获取当前棋盘状态
    """

    def __init__(self) -> None:
        self._moves: List[MoveRecord] = []
        self._metadata: Optional[RecordMetadata] = None
        self._initial_board: Optional[List[List[str]]] = None
        self._current_index: int = -1  # -1 表示初始状态
        self._game: Optional[Game] = None
        self._playing: bool = False
        self._play_thread: Optional[threading.Thread] = None
        self._on_step_callback: Optional[Callable[[int, MoveRecord], None]] = None

    def load(self, record_data: Dict[str, Any]) -> None:
        """加载录像数据。
        
        Args:
            record_data: 录像数据字典
        """
        metadata = record_data.get("metadata", {})
        self._metadata = RecordMetadata(
            game_type=metadata.get("game_type", "unknown"),
            board_size=metadata.get("board_size", 8),
            black_player=metadata.get("black_player", "Unknown"),
            white_player=metadata.get("white_player", "Unknown"),
            start_time=metadata.get("start_time", ""),
            end_time=metadata.get("end_time"),
            result=metadata.get("result"),
            total_moves=metadata.get("total_moves", 0),
            user_id=metadata.get("user_id")
        )

        self._moves = []
        for m in record_data.get("moves", []):
            record = MoveRecord(
                move_number=m["move_number"],
                player=m["player"],
                action_type=m["action_type"],
                position=tuple(m["position"]) if m["position"] else None,
                timestamp=m["timestamp"],
                board_snapshot=m.get("board_snapshot")
            )
            self._moves.append(record)

        self._initial_board = record_data.get("initial_board")
        
        # 初始化游戏
        self._game = GameFactory.create(
            self._metadata.game_type,
            self._metadata.board_size
        )
        
        # 恢复初始棋盘
        if self._initial_board:
            self._restore_board(self._initial_board)
        
        self._current_index = -1

    def load_from_recorder(self, recorder: GameRecorder) -> None:
        """从录像记录器加载。"""
        self.load(recorder.export())

    def next_move(self) -> Optional[MoveRecord]:
        """前进一步。
        
        Returns:
            当前步骤的记录，如果已到末尾返回 None
        """
        if self._current_index >= len(self._moves) - 1:
            return None

        self._current_index += 1
        move = self._moves[self._current_index]
        self._apply_move(move)
        
        if self._on_step_callback:
            self._on_step_callback(self._current_index, move)
        
        return move

    def prev_move(self) -> Optional[MoveRecord]:
        """后退一步。
        
        Returns:
            后退后当前步骤的记录，如果已到开头返回 None
        """
        if self._current_index < 0:
            return None

        target = self._current_index - 1
        self._rebuild_to(target)
        
        if target >= 0:
            return self._moves[target]
        return None

    def jump_to(self, move_number: int) -> None:
        """跳转到指定步数。
        
        Args:
            move_number: 目标步数（1-based），0 表示初始状态
        """
        target = move_number - 1  # 转为索引
        if target < -1 or target >= len(self._moves):
            raise ValueError(f"Invalid move number: {move_number}")
        
        self._rebuild_to(target)

    def _rebuild_to(self, target_index: int) -> None:
        """重建棋盘到指定步骤。"""
        # 找最近的快照
        snapshot_index = -1
        for i in range(target_index, -1, -1):
            if i < len(self._moves) and self._moves[i].board_snapshot is not None:
                snapshot_index = i
                break

        # 从快照或初始状态开始
        if snapshot_index >= 0:
            self._restore_board(self._moves[snapshot_index].board_snapshot)
            start = snapshot_index + 1
        else:
            self._reset_to_initial()
            start = 0

        # 重放到目标
        for i in range(start, target_index + 1):
            self._apply_move(self._moves[i])

        self._current_index = target_index

    def _reset_to_initial(self) -> None:
        """重置到初始状态。"""
        self._game = GameFactory.create(
            self._metadata.game_type,
            self._metadata.board_size
        )
        if self._initial_board:
            self._restore_board(self._initial_board)

    def _restore_board(self, snapshot: List[List[str]]) -> None:
        """从快照恢复棋盘。"""
        for r, row in enumerate(snapshot):
            for c, cell in enumerate(row):
                self._game.board.set(r, c, Stone(cell))

    def _apply_move(self, move: MoveRecord) -> None:
        """应用一步操作到棋盘。"""
        if move.action_type == "move" and move.position:
            row, col = move.position
            player = Stone.BLACK if move.player == "BLACK" else Stone.WHITE
            
            # 对于黑白棋，需要处理翻转
            if self._metadata.game_type.lower() == "othello":
                try:
                    # 临时设置当前玩家
                    self._game.current_player = player
                    self._game.execute_move(row, col)
                except Exception:
                    # 简单落子
                    self._game.board.set(row, col, player)
            else:
                self._game.board.set(row, col, player)
        
        # pass 和 resign 不改变棋盘

    def auto_play(self, interval: float = 1.0, callback: Optional[Callable[[], None]] = None) -> None:
        """自动播放。
        
        Args:
            interval: 每步间隔（秒）
            callback: 每步后的回调函数
        """
        self._playing = True

        def play_loop():
            while self._playing and self._current_index < len(self._moves) - 1:
                self.next_move()
                if callback:
                    callback()
                time.sleep(interval)
            self._playing = False

        self._play_thread = threading.Thread(target=play_loop, daemon=True)
        self._play_thread.start()

    def stop(self) -> None:
        """停止自动播放。"""
        self._playing = False
        if self._play_thread:
            self._play_thread.join(timeout=2.0)
            self._play_thread = None

    def is_playing(self) -> bool:
        """是否正在自动播放。"""
        return self._playing

    def get_current_board(self) -> List[List[Stone]]:
        """获取当前棋盘状态。"""
        if self._game:
            return self._game.board.snapshot()
        return []

    def get_current_move_number(self) -> int:
        """获取当前步数（1-based）。"""
        return self._current_index + 1

    def get_total_moves(self) -> int:
        """获取总步数。"""
        return len(self._moves)

    def get_metadata(self) -> Optional[RecordMetadata]:
        """获取录像元数据。"""
        return self._metadata

    def get_current_move(self) -> Optional[MoveRecord]:
        """获取当前步骤记录。"""
        if 0 <= self._current_index < len(self._moves):
            return self._moves[self._current_index]
        return None

    def get_game(self) -> Optional[Game]:
        """获取游戏对象（用于渲染）。"""
        return self._game

    def set_step_callback(self, callback: Callable[[int, MoveRecord], None]) -> None:
        """设置步进回调。"""
        self._on_step_callback = callback
