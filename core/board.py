"""Board and stone related classes."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterator, List, Tuple


class Stone(str, Enum):
    """Possible board cell states."""

    EMPTY = "."
    BLACK = "B"
    WHITE = "W"

    def opposite(self) -> "Stone":
        if self == Stone.BLACK:
            return Stone.WHITE
        if self == Stone.WHITE:
            return Stone.BLACK
        return Stone.EMPTY


@dataclass(frozen=True)
class Position:
    row: int
    col: int


class Board:
    """Represents a square board."""

    def __init__(self, size: int) -> None:
        if size < 8 or size > 19:
            raise ValueError("Board size must be between 8 and 19.")
        self.size = size
        self.grid: List[List[Stone]] = [
            [Stone.EMPTY for _ in range(size)] for _ in range(size)
        ]

    def clear(self) -> None:
        for r in range(self.size):
            for c in range(self.size):
                self.grid[r][c] = Stone.EMPTY

    def is_on_board(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def get(self, row: int, col: int) -> Stone:
        return self.grid[row][col]

    def set(self, row: int, col: int, stone: Stone) -> None:
        self.grid[row][col] = stone

    def is_empty(self, row: int, col: int) -> bool:
        return self.get(row, col) == Stone.EMPTY

    def neighbors(self, row: int, col: int) -> Iterator[Tuple[int, int]]:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, col + dc
            if self.is_on_board(nr, nc):
                yield nr, nc

    def count_stones(self, stone: Stone) -> int:
        return sum(cell == stone for row in self.grid for cell in row)

    def snapshot(self) -> List[List[Stone]]:
        """Return a deep copy of the grid."""
        return [[cell for cell in row] for row in self.grid]

    def restore(self, snapshot: List[List[Stone]]) -> None:
        if len(snapshot) != self.size:
            raise ValueError("Snapshot size mismatch.")
        self.grid = [[cell for cell in row] for row in snapshot]

