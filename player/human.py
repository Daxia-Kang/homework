"""Human player implementation."""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional

from player.base import IPlayer, PlayerType, PlayerAction, ActionType, GameResult

if TYPE_CHECKING:
    from core.game import Game
    from account.models import User


class HumanPlayer(IPlayer):
    """人类玩家实现。
    
    通过输入处理器获取玩家输入，支持关联用户账户。
    """

    def __init__(
        self,
        name: str,
        input_handler: Optional[Callable[["Game"], PlayerAction]] = None,
        user: Optional["User"] = None
    ) -> None:
        """初始化人类玩家。
        
        Args:
            name: 玩家名称
            input_handler: 输入处理函数，接收游戏状态返回动作
            user: 关联的用户账户（可选）
        """
        self._name = name
        self._input_handler = input_handler
        self._user = user
        self._player_type = PlayerType.HUMAN

    @property
    def name(self) -> str:
        return self._name

    @property
    def player_type(self) -> PlayerType:
        return self._player_type

    @property
    def user(self) -> Optional["User"]:
        """关联的用户账户。"""
        return self._user

    def get_action(self, game: "Game") -> PlayerAction:
        """获取人类玩家的动作。
        
        如果设置了输入处理器，通过处理器获取；
        否则抛出异常（需要外部设置输入处理器）。
        """
        if self._input_handler is None:
            raise RuntimeError("Human player requires an input handler")
        return self._input_handler(game)

    def set_input_handler(self, handler: Callable[["Game"], PlayerAction]) -> None:
        """设置输入处理器。"""
        self._input_handler = handler

    def notify_result(self, result: GameResult) -> None:
        """通知游戏结果（人类玩家通常通过 UI 展示）。"""
        pass


class GuestPlayer(HumanPlayer):
    """游客玩家（未登录的人类玩家）。"""

    def __init__(
        self,
        input_handler: Optional[Callable[["Game"], PlayerAction]] = None
    ) -> None:
        super().__init__("Guest", input_handler, None)
