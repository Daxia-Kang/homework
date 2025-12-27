"""AI base classes and interfaces.

设计模式：策略模式
- IMoveStrategy 是策略接口
- 具体策略（RandomStrategy, EvalStrategy）实现不同的落子算法
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from core.game import Game


class AIDifficulty(Enum):
    """AI 难度等级。"""
    EASY = 1      # 随机落子
    MEDIUM = 2    # 评分函数
    HARD = 3      # MCTS（可选）


class IMoveStrategy(ABC):
    """落子策略接口。
    
    设计模式：策略模式
    - 定义落子算法的统一接口
    - 具体策略类实现不同的落子逻辑
    """

    @abstractmethod
    def select_move(self, game: "Game") -> Tuple[int, int]:
        """选择落子位置。
        
        Args:
            game: 当前游戏状态
            
        Returns:
            (row, col) 落子坐标
        """
        ...

    @property
    def name(self) -> str:
        """策略名称。"""
        return self.__class__.__name__


class IAI(ABC):
    """AI 玩家扩展接口。"""

    @property
    @abstractmethod
    def difficulty(self) -> AIDifficulty:
        """AI 难度等级。"""
        ...

    @abstractmethod
    def select_move(self, game: "Game") -> Tuple[int, int]:
        """选择落子位置。"""
        ...
