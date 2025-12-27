"""Player base classes and interfaces.

设计模式：策略模式
- IPlayer 接口统一人类/AI/远程玩家
- 对局控制器无需关心具体玩家类型
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.game import Game


class PlayerType(Enum):
    """玩家类型枚举。"""
    HUMAN = "human"
    AI = "ai"
    REMOTE = "remote"


class ActionType(Enum):
    """玩家动作类型枚举。"""
    MOVE = "move"
    PASS = "pass"
    RESIGN = "resign"
    UNDO = "undo"


@dataclass
class PlayerAction:
    """玩家动作统一表示。
    
    Attributes:
        action_type: 动作类型
        row: 落子行坐标（仅 MOVE 时有效）
        col: 落子列坐标（仅 MOVE 时有效）
    """
    action_type: ActionType
    row: Optional[int] = None
    col: Optional[int] = None

    @classmethod
    def move(cls, row: int, col: int) -> "PlayerAction":
        """创建落子动作。"""
        return cls(ActionType.MOVE, row, col)

    @classmethod
    def pass_turn(cls) -> "PlayerAction":
        """创建 pass 动作。"""
        return cls(ActionType.PASS)

    @classmethod
    def resign(cls) -> "PlayerAction":
        """创建认输动作。"""
        return cls(ActionType.RESIGN)

    @classmethod
    def undo(cls) -> "PlayerAction":
        """创建悔棋动作。"""
        return cls(ActionType.UNDO)


@dataclass
class GameResult:
    """游戏结果。
    
    Attributes:
        is_win: 是否获胜
        is_draw: 是否平局
        opponent_name: 对手名称
    """
    is_win: bool
    is_draw: bool
    opponent_name: str


class IPlayer(ABC):
    """玩家抽象接口。
    
    统一人类玩家、AI 玩家、远程玩家的接口。
    对局控制器通过此接口与玩家交互，无需关心具体实现。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """玩家名称。"""
        ...

    @property
    @abstractmethod
    def player_type(self) -> PlayerType:
        """玩家类型。"""
        ...

    @abstractmethod
    def get_action(self, game: "Game") -> PlayerAction:
        """获取玩家的下一步动作。
        
        Args:
            game: 当前游戏状态
            
        Returns:
            玩家选择的动作
        """
        ...

    @abstractmethod
    def notify_result(self, result: GameResult) -> None:
        """通知玩家游戏结果。
        
        Args:
            result: 游戏结果
        """
        ...

    def notify_opponent_action(self, action: PlayerAction) -> None:
        """通知玩家对手的动作（可选实现）。
        
        主要用于远程玩家同步。
        
        Args:
            action: 对手的动作
        """
        pass
