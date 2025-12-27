"""Match controller - 对局控制器。

协调玩家与游戏的交互，管理对局流程。
设计模式：观察者模式 - 对局事件通知 UI、录像器等观察者。
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from core.board import Stone
from core.game import (
    Game, GameFactory, GameError,
    MoveCommand, PassCommand, ResignCommand
)
from player.base import IPlayer, PlayerAction, ActionType, GameResult, PlayerType
from match.recorder import GameRecorder

if TYPE_CHECKING:
    pass


@dataclass
class TurnResult:
    """回合结果。"""
    player: Stone
    player_name: str
    action: PlayerAction
    message: str
    game_over: bool


@dataclass
class MatchResult:
    """对局结果。"""
    winner: Optional[Stone]
    winner_name: Optional[str]
    black_player: str
    white_player: str
    move_count: int
    game_type: str


@dataclass
class MoveEvent:
    """落子事件。"""
    player: IPlayer
    action: PlayerAction
    message: str


@dataclass
class GameOverEvent:
    """游戏结束事件。"""
    result: MatchResult


class IMatchObserver(ABC):
    """对局观察者接口。
    
    设计模式：观察者模式
    - 观察者接收对局事件通知
    - UI、录像器等实现此接口
    """

    @abstractmethod
    def on_move(self, event: MoveEvent) -> None:
        """落子事件回调。"""
        ...

    @abstractmethod
    def on_game_over(self, event: GameOverEvent) -> None:
        """游戏结束事件回调。"""
        ...


class MatchController:
    """对局控制器。
    
    职责：
    1. 协调玩家与游戏的交互
    2. 管理对局流程
    3. 记录对局过程
    4. 通知观察者
    
    设计模式：
    - 观察者模式：通知 UI、录像器等
    - 中介者模式：协调玩家与游戏
    """

    def __init__(self) -> None:
        self.game: Optional[Game] = None
        self.black_player: Optional[IPlayer] = None
        self.white_player: Optional[IPlayer] = None
        self.recorder: Optional[GameRecorder] = None
        self._observers: List[IMatchObserver] = []
        self._on_turn_callback: Optional[Callable[[TurnResult], None]] = None

    def start(
        self,
        game_type: str,
        size: int,
        black_player: IPlayer,
        white_player: IPlayer,
        user_id: Optional[str] = None
    ) -> None:
        """开始新对局。
        
        Args:
            game_type: 游戏类型
            size: 棋盘大小
            black_player: 黑方玩家
            white_player: 白方玩家
            user_id: 关联的用户 ID
        """
        self.game = GameFactory.create(game_type, size)
        self.black_player = black_player
        self.white_player = white_player
        
        # 创建录像记录器
        self.recorder = GameRecorder(
            game_type=game_type,
            board_size=size,
            black_player=black_player.name,
            white_player=white_player.name,
            user_id=user_id
        )
        self.recorder.set_initial_board(self.game.board.snapshot())

    def get_current_player(self) -> IPlayer:
        """获取当前行棋方的玩家对象。"""
        if self.game is None:
            raise GameError("No game in progress")
        if self.game.current_player == Stone.BLACK:
            return self.black_player
        return self.white_player

    def play_turn(self) -> TurnResult:
        """执行一个回合。
        
        Returns:
            回合结果
        """
        if self.game is None:
            raise GameError("No game in progress")
        if self.game.is_over:
            raise GameError("Game already ended")

        current = self.get_current_player()
        
        # 获取玩家动作
        action = current.get_action(self.game)
        
        # 执行动作
        message = self._execute_action(action)
        
        # 记录
        if self.recorder:
            self.recorder.record_move(
                action,
                self.game.current_player if not self.game.is_over else 
                    (Stone.BLACK if self.game.current_player == Stone.WHITE else Stone.WHITE),
                self.game.board.snapshot(),
                time.time()
            )
        
        # 通知观察者
        self._notify_move(MoveEvent(current, action, message))
        
        result = TurnResult(
            player=self.game.current_player,
            player_name=current.name,
            action=action,
            message=message,
            game_over=self.game.is_over
        )
        
        # 如果游戏结束，处理结果
        if self.game.is_over:
            self._handle_game_over()
        
        return result

    def play_action(self, action: PlayerAction) -> TurnResult:
        """执行指定动作（供 UI 直接调用）。
        
        Args:
            action: 玩家动作
            
        Returns:
            回合结果
        """
        if self.game is None:
            raise GameError("No game in progress")
        if self.game.is_over:
            raise GameError("Game already ended")

        current = self.get_current_player()
        pre_player = self.game.current_player
        
        # 执行动作
        message = self._execute_action(action)
        
        # 记录
        if self.recorder:
            self.recorder.record_move(
                action, pre_player,
                self.game.board.snapshot(),
                time.time()
            )
        
        result = TurnResult(
            player=pre_player,
            player_name=current.name,
            action=action,
            message=message,
            game_over=self.game.is_over
        )
        
        if self.game.is_over:
            self._handle_game_over()
        
        return result

    def _execute_action(self, action: PlayerAction) -> str:
        """执行玩家动作。"""
        if action.action_type == ActionType.MOVE:
            cmd = MoveCommand(self.game, action.row, action.col)
        elif action.action_type == ActionType.PASS:
            cmd = PassCommand(self.game)
        elif action.action_type == ActionType.RESIGN:
            cmd = ResignCommand(self.game)
        elif action.action_type == ActionType.UNDO:
            last = self.game.pop_history()
            if last:
                return last.undo()
            return "No moves to undo."
        else:
            raise GameError(f"Unknown action: {action.action_type}")

        message = cmd.execute()
        if action.action_type != ActionType.UNDO:
            self.game.add_history(cmd)
        return message

    def undo(self) -> str:
        """执行悔棋。"""
        if self.game is None:
            raise GameError("No game in progress")
        last = self.game.pop_history()
        if not last:
            return "No moves to undo."
        return last.undo()

    def is_finished(self) -> bool:
        """检查对局是否结束。"""
        return self.game is not None and self.game.is_over

    def get_result(self) -> MatchResult:
        """获取对局结果。"""
        if self.game is None:
            raise GameError("No game in progress")
        
        winner_name = None
        if self.game.winner == Stone.BLACK:
            winner_name = self.black_player.name
        elif self.game.winner == Stone.WHITE:
            winner_name = self.white_player.name
        
        return MatchResult(
            winner=self.game.winner,
            winner_name=winner_name,
            black_player=self.black_player.name,
            white_player=self.white_player.name,
            move_count=len(self.game.history),
            game_type=self.game.name.lower()
        )

    def get_recorder(self) -> Optional[GameRecorder]:
        """获取录像记录器。"""
        return self.recorder

    def _handle_game_over(self) -> None:
        """处理游戏结束。"""
        result = self.get_result()
        
        # 完成录像
        if self.recorder:
            result_str = "DRAW"
            if result.winner == Stone.BLACK:
                result_str = "BLACK_WIN"
            elif result.winner == Stone.WHITE:
                result_str = "WHITE_WIN"
            self.recorder.finalize(result_str, self.game.board.snapshot())
        
        # 通知玩家
        black_result = GameResult(
            is_win=(result.winner == Stone.BLACK),
            is_draw=(result.winner is None),
            opponent_name=self.white_player.name
        )
        white_result = GameResult(
            is_win=(result.winner == Stone.WHITE),
            is_draw=(result.winner is None),
            opponent_name=self.black_player.name
        )
        
        self.black_player.notify_result(black_result)
        self.white_player.notify_result(white_result)
        
        # 通知观察者
        self._notify_game_over(GameOverEvent(result))

    # ==================== 观察者模式方法 ====================

    def add_observer(self, observer: IMatchObserver) -> None:
        """添加观察者。"""
        self._observers.append(observer)

    def remove_observer(self, observer: IMatchObserver) -> None:
        """移除观察者。"""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_move(self, event: MoveEvent) -> None:
        """通知落子事件。"""
        for observer in self._observers:
            observer.on_move(event)

    def _notify_game_over(self, event: GameOverEvent) -> None:
        """通知游戏结束事件。"""
        for observer in self._observers:
            observer.on_game_over(event)

    def set_turn_callback(self, callback: Callable[[TurnResult], None]) -> None:
        """设置回合回调（简化版观察者）。"""
        self._on_turn_callback = callback
