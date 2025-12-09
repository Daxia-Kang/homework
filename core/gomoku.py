"""Gomoku implementation."""
from __future__ import annotations

from typing import List, Tuple

from core.board import Board, Stone
from core.game import Game, GameError, GameState, MoveDelta


class GomokuGame(Game):
    """Concrete Gomoku game logic."""

    name = "Gomoku"

    def _apply_move(
        self, row: int, col: int, player: Stone, pre_state: GameState
    ) -> MoveDelta:
        self.board.set(row, col, player)
        message = f"{player.name} moves to ({row + 1}, {col + 1})."
        return MoveDelta(
            row=row,
            col=col,
            player=player,
            captured=[],
            message=message,
            pre_state=pre_state,
        )

    def _post_move(self, delta: MoveDelta) -> None:
        if self._check_five_in_row(delta.row, delta.col, delta.player):
            self.winner = delta.player
            self.is_over = True
        elif self._is_board_full():
            self.winner = None
            self.is_over = True

    def undo_move(self, delta: MoveDelta) -> None:
        self.board.set(delta.row, delta.col, Stone.EMPTY)
        self.restore_state(delta.pre_state)

    def _check_five_in_row(self, row: int, col: int, player: Stone) -> bool:
        directions: List[Tuple[int, int]] = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dr, dc in directions:
            if self._count_direction(row, col, dr, dc, player) >= 5:
                return True
        return False

    def _count_direction(
        self, row: int, col: int, dr: int, dc: int, player: Stone
    ) -> int:
        count = 1
        r, c = row + dr, col + dc
        while self.board.is_on_board(r, c) and self.board.get(r, c) == player:
            count += 1
            r += dr
            c += dc
        r, c = row - dr, col - dc
        while self.board.is_on_board(r, c) and self.board.get(r, c) == player:
            count += 1
            r -= dr
            c -= dc
        return count

    def _is_board_full(self) -> bool:
        return all(cell != Stone.EMPTY for row in self.board.grid for cell in row)

