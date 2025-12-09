"""Save and load game state using JSON."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from core.board import Stone
from core.game import Game, GameError, GameFactory


def serialize_board(game: Game) -> List[List[str]]:
    return [[cell.value for cell in row] for row in game.board.grid]


def deserialize_board(game: Game, grid: List[List[str]]) -> None:
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


def save_game(game: Game, filename: str) -> None:
    data: Dict[str, Any] = {
        "game_type": game.name.lower(),
        "size": game.board.size,
        "current_player": game.current_player.value,
        "winner": game.winner.value if game.winner else None,
        "is_over": game.is_over,
        "pass_count": game.pass_count,
        "board": serialize_board(game),
    }
    try:
        Path(filename).write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as exc:
        raise GameError(f"Failed to save: {exc}") from exc


def load_game(filename: str) -> Game:
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
    game.history.clear()  # start fresh after loading
    return game

