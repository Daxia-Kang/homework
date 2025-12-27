"""Player module - 玩家抽象层。

提供统一的玩家接口，支持人类玩家、AI 玩家、远程玩家。
设计模式：策略模式 - 不同类型的玩家使用相同接口。
"""
from player.base import IPlayer, PlayerType, PlayerAction, ActionType, GameResult
from player.human import HumanPlayer

__all__ = [
    "IPlayer",
    "PlayerType", 
    "PlayerAction",
    "ActionType",
    "GameResult",
    "HumanPlayer",
]
