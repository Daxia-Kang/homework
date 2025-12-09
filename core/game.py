"""Abstract game definitions and shared logic."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple

from core.board import Board, Stone


class GameError(Exception):
    """Raised when a user-facing game error occurs."""


@dataclass
class GameState:
    current_player: Stone
    winner: Optional[Stone]
    is_over: bool
    pass_count: int


@dataclass
class MoveDelta:
    row: int
    col: int
    player: Stone
    captured: List[Tuple[int, int, Stone]]
    message: str
    pre_state: GameState


@dataclass
class PassRecord:
    player: Stone
    message: str
    pre_state: GameState


@dataclass
class ResignRecord:
    player: Stone
    message: str
    pre_state: GameState


class Game(ABC):
    """Template for games that share turn-based flow."""

    def __init__(self, size: int) -> None:
        self.board = Board(size)
        self.current_player: Stone = Stone.BLACK
        self.winner: Optional[Stone] = None
        self.is_over: bool = False
        self.pass_count: int = 0  # used by Go
        self.history: List["Command"] = []

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    def record_state(self) -> GameState:
        return GameState(
            current_player=self.current_player,
            winner=self.winner,
            is_over=self.is_over,
            pass_count=self.pass_count,
        )

    def restore_state(self, state: GameState) -> None:
        self.current_player = state.current_player
        self.winner = state.winner
        self.is_over = state.is_over
        self.pass_count = state.pass_count

    def switch_player(self) -> None:
        self.current_player = (
            Stone.BLACK if self.current_player == Stone.WHITE else Stone.WHITE
        )

    def execute_move(self, row: int, col: int) -> MoveDelta:
        if self.is_over:
            raise GameError("Game already ended.")
        if not self.board.is_on_board(row, col):
            raise GameError("Move out of board range.")
        if not self.board.is_empty(row, col):
            raise GameError("Cell is already occupied.")

        pre_state = self.record_state()
        delta = self._apply_move(row, col, self.current_player, pre_state)
        self._post_move(delta)
        if not self.is_over:
            self.switch_player()
        return delta

    @abstractmethod
    def _apply_move(
        self, row: int, col: int, player: Stone, pre_state: GameState
    ) -> MoveDelta:
        ...

    @abstractmethod
    def _post_move(self, delta: MoveDelta) -> None:
        ...

    @abstractmethod
    def undo_move(self, delta: MoveDelta) -> None:
        ...

    def execute_pass(self) -> PassRecord:
        raise GameError(f"{self.name} does not support pass.")

    def undo_pass(self, record: PassRecord) -> None:
        raise GameError("Nothing to undo.")

    def execute_resign(self) -> ResignRecord:
        if self.is_over:
            raise GameError("Game already ended.")
        record = ResignRecord(
            player=self.current_player,
            message=f"{self.current_player.name} resigns.",
            pre_state=self.record_state(),
        )
        self.winner = self.current_player.opposite()
        self.is_over = True
        return record

    def undo_resign(self, record: ResignRecord) -> None:
        self.restore_state(record.pre_state)

    def can_undo(self) -> bool:
        return bool(self.history)

    def add_history(self, cmd: "Command") -> None:
        self.history.append(cmd)

    def pop_history(self) -> Optional["Command"]:
        return self.history.pop() if self.history else None


class Command(ABC):
    """Command pattern base."""

    def __init__(self, game: Game) -> None:
        self.game = game

    @abstractmethod
    def execute(self) -> str:
        ...

    @abstractmethod
    def undo(self) -> str:
        ...


class MoveCommand(Command):
    def __init__(self, game: Game, row: int, col: int) -> None:
        super().__init__(game)
        self.row = row
        self.col = col
        self.delta: Optional[MoveDelta] = None

    def execute(self) -> str:
        self.delta = self.game.execute_move(self.row, self.col)
        return self.delta.message

    def undo(self) -> str:
        if not self.delta:
            return "No move to undo."
        self.game.undo_move(self.delta)
        return "Move undone."


class PassCommand(Command):
    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self.record: Optional[PassRecord] = None

    def execute(self) -> str:
        self.record = self.game.execute_pass()
        return self.record.message

    def undo(self) -> str:
        if not self.record:
            return "Nothing to undo."
        self.game.undo_pass(self.record)
        return "Pass undone."


class ResignCommand(Command):
    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self.record: Optional[ResignRecord] = None

    def execute(self) -> str:
        self.record = self.game.execute_resign()
        return self.record.message

    def undo(self) -> str:
        if not self.record:
            return "Nothing to undo."
        self.game.undo_resign(self.record)
        return "Resign undone."


class GameFactory:
    """Simple factory to build games based on type string."""

    @staticmethod
    def create(game_type: str, size: int) -> Game:
        normalized = game_type.lower()
        if normalized == "gomoku":
            from core.gomoku import GomokuGame

            return GomokuGame(size)
        if normalized == "go":
            from core.go import GoGame

            return GoGame(size)
        raise GameError(f"Unknown game type: {game_type}")
