"""AI player module - AI 玩家实现。

设计模式：策略模式
- IMoveStrategy 定义落子策略接口
- 不同难度 AI 实现不同策略
- AIPlayer 持有策略对象，可运行时切换
"""
from player.ai.base import IAI, IMoveStrategy, AIDifficulty
from player.ai.random_ai import RandomStrategy
from player.ai.eval_ai import AIPlayer, EvalStrategyFactory

__all__ = [
    "IAI",
    "IMoveStrategy", 
    "AIDifficulty",
    "RandomStrategy",
    "AIPlayer",
    "EvalStrategyFactory",
]
