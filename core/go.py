"""Simplified Go implementation with capture and pass."""
from __future__ import annotations

from collections import deque
from typing import Dict, List, Set, Tuple

from core.board import Board, Stone
from core.game import Game, GameError, GameState, MoveDelta, PassRecord


class GoGame(Game):
    """Concrete Go game logic with simple area scoring."""

    name = "Go"

    def _apply_move(
        self, row: int, col: int, player: Stone, pre_state: GameState
    ) -> MoveDelta:
        opponent = player.opposite()
        captured: List[Tuple[int, int, Stone]] = []
        self.board.set(row, col, player)

        for nr, nc in self.board.neighbors(row, col):
            if self.board.get(nr, nc) == opponent:
                group, liberties = self._collect_group(nr, nc)
                if liberties == 0:
                    for gr, gc in group:
                        captured.append((gr, gc, opponent))
                        self.board.set(gr, gc, Stone.EMPTY)

        # Check for suicide (no liberties after captures)
        _, liberties_after = self._collect_group(row, col)
        if liberties_after == 0:
            # revert placement
            self.board.set(row, col, Stone.EMPTY)
            for gr, gc, color in captured:
                self.board.set(gr, gc, color)
            raise GameError("Illegal self-capture (suicide) move.")

        message = f"{player.name} moves to ({row + 1}, {col + 1})."
        return MoveDelta(
            row=row,
            col=col,
            player=player,
            captured=captured,
            message=message,
            pre_state=pre_state,
        )

    def _post_move(self, delta: MoveDelta) -> None:
        self.pass_count = 0
        if self._is_board_full():
            self._finalize_score()

    def undo_move(self, delta: MoveDelta) -> None:
        self.board.set(delta.row, delta.col, Stone.EMPTY)
        for r, c, color in delta.captured:
            self.board.set(r, c, color)
        self.restore_state(delta.pre_state)

    def execute_pass(self) -> PassRecord:
        if self.is_over:
            raise GameError("Game already ended.")
        record = PassRecord(
            player=self.current_player,
            message=f"{self.current_player.name} passes.",
            pre_state=self.record_state(),
        )
        self.pass_count += 1
        if self.pass_count >= 2:
            self._finalize_score()
        if not self.is_over:
            self.switch_player()
        return record

    def undo_pass(self, record: PassRecord) -> None:
        self.restore_state(record.pre_state)

    def _collect_group(self, row: int, col: int) -> Tuple[Set[Tuple[int, int]], int]:
        """Return group positions and liberty count."""
        color = self.board.get(row, col)
        if color == Stone.EMPTY:
            return set(), 0
        visited: Set[Tuple[int, int]] = set()
        liberties = 0
        queue: deque[Tuple[int, int]] = deque()
        queue.append((row, col))
        visited.add((row, col))
        while queue:
            r, c = queue.popleft()
            for nr, nc in self.board.neighbors(r, c):
                cell = self.board.get(nr, nc)
                if cell == Stone.EMPTY:
                    liberties += 1
                elif cell == color and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return visited, liberties

    def _is_board_full(self) -> bool:
        return all(cell != Stone.EMPTY for row in self.board.grid for cell in row)

    def _finalize_score(self) -> None:
        black_score, white_score = self._calculate_area_score()
        if black_score > white_score:
            self.winner = Stone.BLACK
        elif white_score > black_score:
            self.winner = Stone.WHITE
        else:
            self.winner = None
        self.is_over = True

    def _calculate_area_score(self) -> Tuple[int, int]:
        """Simple area scoring: stones + exclusive empty territories."""
        black = self.board.count_stones(Stone.BLACK)
        white = self.board.count_stones(Stone.WHITE)
        visited: Set[Tuple[int, int]] = set()

        for r in range(self.board.size):
            for c in range(self.board.size):
                if self.board.get(r, c) != Stone.EMPTY or (r, c) in visited:
                    continue
                region, owners = self._explore_empty_region(r, c, visited)
                if len(owners) == 1:
                    owner = owners.pop()
                    if owner == Stone.BLACK:
                        black += len(region)
                    elif owner == Stone.WHITE:
                        white += len(region)
        return black, white

    def _explore_empty_region(
        self, row: int, col: int, visited: Set[Tuple[int, int]]
    ) -> Tuple[List[Tuple[int, int]], Set[Stone]]:
        region: List[Tuple[int, int]] = []
        owners: Set[Stone] = set()
        queue: deque[Tuple[int, int]] = deque()
        queue.append((row, col))
        visited.add((row, col))
        while queue:
            r, c = queue.popleft()
            region.append((r, c))
            for nr, nc in self.board.neighbors(r, c):
                cell = self.board.get(nr, nc)
                if cell == Stone.EMPTY and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
                elif cell != Stone.EMPTY:
                    owners.add(cell)
        return region, owners

