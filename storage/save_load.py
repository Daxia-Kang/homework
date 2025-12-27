"""Save and load game state using JSON.

扩展支持：
1. 基本存档（兼容第一阶段）
2. 带录像的存档
3. 纯录像文件
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.board import Stone
from core.game import Game, GameError, GameFactory


def serialize_board(game: Game) -> List[List[str]]:
    """序列化棋盘。"""
    return [[cell.value for cell in row] for row in game.board.grid]


def deserialize_board(game: Game, grid: List[List[str]]) -> None:
    """反序列化棋盘。"""
    if len(grid) != game.board.size:
        raise GameError("Saved board size does not match.")
    for r, row in enumerate(grid):
        if len(row) != game.board.size:
            raise GameError("Saved board size does not match.")
        for c, val in enumerate(row):
            try:
                stone = Stone(val)
            except ValueError as exc:
                raise GameError("Invalid stone in save file.") from exc
            game.board.set(r, c, stone)


def save_game(
    game: Game,
    filename: str,
    replay_data: Optional[Dict[str, Any]] = None
) -> None:
    """保存游戏状态。
    
    Args:
        game: 游戏对象
        filename: 文件名
        replay_data: 可选的录像数据
    """
    data: Dict[str, Any] = {
        "version": "2.0",
        "game_type": game.name.lower(),
        "size": game.board.size,
        "current_player": game.current_player.value,
        "winner": game.winner.value if game.winner else None,
        "is_over": game.is_over,
        "pass_count": game.pass_count,
        "board": serialize_board(game),
    }
    
    # 如果有录像数据，合并进去
    if replay_data:
        data["replay"] = replay_data
    
    try:
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        raise GameError(f"Failed to save: {exc}") from exc


def load_game(filename: str) -> Tuple[Game, Optional[Dict[str, Any]]]:
    """加载游戏状态。
    
    Args:
        filename: 文件名
        
    Returns:
        (游戏对象, 录像数据或 None)
    """
    path = Path(filename)
    if not path.exists():
        raise GameError("Save file not found.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GameError(f"Failed to read save file: {exc}") from exc

    required = {"game_type", "size", "current_player", "board"}
    if not required.issubset(data):
        raise GameError("Save file missing required fields.")

    game = GameFactory.create(data["game_type"], int(data["size"]))
    deserialize_board(game, data["board"])
    try:
        game.current_player = Stone(data["current_player"])
    except ValueError as exc:
        raise GameError("Invalid player in save file.") from exc
    game.is_over = bool(data.get("is_over", False))
    winner_val = data.get("winner")
    game.winner = Stone(winner_val) if winner_val else None
    game.pass_count = int(data.get("pass_count", 0))
    game.history.clear()
    
    replay_data = data.get("replay")
    return game, replay_data


def save_replay(replay_data: Dict[str, Any], filename: str) -> None:
    """保存纯录像文件。
    
    Args:
        replay_data: 录像数据
        filename: 文件名
    """
    try:
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(replay_data, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        raise GameError(f"Failed to save replay: {exc}") from exc


def load_replay(filename: str) -> Dict[str, Any]:
    """加载录像文件。
    
    Args:
        filename: 文件名
        
    Returns:
        录像数据
    """
    path = Path(filename)
    if not path.exists():
        raise GameError("Replay file not found.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GameError(f"Failed to read replay file: {exc}") from exc
    
    # 检查是否是带录像的存档
    if "replay" in data:
        return data["replay"]
    
    # 检查是否是纯录像文件
    if "metadata" in data and "moves" in data:
        return data
    
    raise GameError("Invalid replay file format.")


# 兼容第一阶段的简化接口
def load_game_simple(filename: str) -> Game:
    """加载游戏（兼容第一阶段）。"""
    game, _ = load_game(filename)
    return game


