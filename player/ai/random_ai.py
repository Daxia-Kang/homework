"""Random AI strategy - 一级随机 AI。

最简单的 AI 策略：在所有合法位置中随机选择一个。
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Tuple

from player.ai.base import IMoveStrategy

if TYPE_CHECKING:
    from core.game import Game


class RandomStrategy(IMoveStrategy):
    """一级 AI：随机选择合法位置。
    
    实现最简单的落子策略，作为基准 AI。
    """

    def select_move(self, game: "Game") -> Tuple[int, int]:
        """在合法位置中随机选择一个。
        
        Args:
            game: 当前游戏状态
            
        Returns:
            随机选择的合法位置 (row, col)
            
        Raises:
            ValueError: 没有合法落子位置
        """
        legal_moves = game.get_legal_moves()
        if not legal_moves:
            raise ValueError("No legal moves available")
        return random.choice(legal_moves)

    @property
    def name(self) -> str:
        return "Random"
