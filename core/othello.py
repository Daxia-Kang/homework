"""Othello (Reversi) implementation.

黑白棋规则：
1. 棋盘默认 8×8，初始中央 4 子
2. 只能在合法位置落子（必须能翻转至少一个对方棋子）
3. 落子后翻转所有被夹住的对方棋子（8 个方向）
4. 若一方无合法棋步，本回合被迫弃权（pass）
5. 棋盘填满或双方均无合法棋步时，子数多者胜
"""
from __future__ import annotations

from typing import List, Tuple

from core.board import Board, Stone
from core.game import Game, GameError, GameState, MoveDelta, PassRecord


# 8 个方向：上、下、左、右、4 个对角
DIRECTIONS: List[Tuple[int, int]] = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
]


class OthelloGame(Game):
    """黑白棋游戏实现。
    
    设计模式：模板方法模式
    - 继承 Game 基类，实现黑白棋特有的规则
    - 重写 get_legal_moves() 和 must_pass() 以支持黑白棋的强制 pass
    """

    name = "Othello"
    DEFAULT_SIZE = 8

    def __init__(self, size: int = 8) -> None:
        """初始化黑白棋游戏。
        
        Args:
            size: 棋盘大小，标准为 8，支持 4-19
        """
        super().__init__(size)
        self._setup_initial_position()

    def _setup_initial_position(self) -> None:
        """设置初始局面：中央 4 子交叉放置。"""
        mid = self.board.size // 2
        self.board.set(mid - 1, mid - 1, Stone.WHITE)
        self.board.set(mid - 1, mid, Stone.BLACK)
        self.board.set(mid, mid - 1, Stone.BLACK)
        self.board.set(mid, mid, Stone.WHITE)

    def is_legal_move(self, row: int, col: int, player: Stone) -> bool:
        """判断 (row, col) 对于 player 是否为合法落子位置。
        
        合法条件：
        1. 在棋盘内
        2. 是空位
        3. 至少在一个方向上能翻转对方棋子
        """
        if not self.board.is_on_board(row, col):
            return False
        if not self.board.is_empty(row, col):
            return False
        
        opponent = player.opposite()
        for dr, dc in DIRECTIONS:
            if self._can_flip_in_direction(row, col, dr, dc, player, opponent):
                return True
        return False

    def _can_flip_in_direction(self, row: int, col: int,
                                dr: int, dc: int,
                                player: Stone, opponent: Stone) -> bool:
        """检查在 (dr, dc) 方向上是否能翻转。
        
        翻转条件：从落子位置出发，先遇到连续的对方棋子，再遇到己方棋子。
        """
        r, c = row + dr, col + dc
        found_opponent = False
        
        while self.board.is_on_board(r, c):
            cell = self.board.get(r, c)
            if cell == opponent:
                found_opponent = True
                r += dr
                c += dc
            elif cell == player:
                return found_opponent
            else:
                # 遇到空位
                break
        return False

    def _collect_flips_in_direction(self, row: int, col: int,
                                     dr: int, dc: int,
                                     player: Stone, opponent: Stone) -> List[Tuple[int, int]]:
        """收集某方向上需要翻转的棋子坐标。"""
        to_flip: List[Tuple[int, int]] = []
        r, c = row + dr, col + dc
        
        while self.board.is_on_board(r, c):
            cell = self.board.get(r, c)
            if cell == opponent:
                to_flip.append((r, c))
                r += dr
                c += dc
            elif cell == player:
                return to_flip
            else:
                return []
        return []

    def execute_move(self, row: int, col: int) -> MoveDelta:
        """执行落子（重写以添加黑白棋特有的合法性检查）。"""
        if self.is_over:
            raise GameError("Game already ended.")
        if not self.board.is_on_board(row, col):
            raise GameError("Move out of board range.")
        if not self.is_legal_move(row, col, self.current_player):
            raise GameError("Illegal move: must flip at least one opponent stone.")
        
        pre_state = self.record_state()
        delta = self._apply_move(row, col, self.current_player, pre_state)
        self._post_move(delta)
        if not self.is_over:
            self.switch_player()
            # 如果对手无合法落子，检查是否游戏结束
            if self.must_pass():
                # 对手无法落子，再切回来
                self.switch_player()
                if self.must_pass():
                    # 双方都无法落子，游戏结束
                    self._finalize_score()
        return delta

    def _apply_move(self, row: int, col: int, player: Stone,
                    pre_state: GameState) -> MoveDelta:
        """落子并翻转被夹住的对方棋子。"""
        opponent = player.opposite()
        flipped: List[Tuple[int, int, Stone]] = []
        
        # 放置棋子
        self.board.set(row, col, player)
        
        # 8 个方向翻转
        for dr, dc in DIRECTIONS:
            to_flip = self._collect_flips_in_direction(row, col, dr, dc, player, opponent)
            for fr, fc in to_flip:
                self.board.set(fr, fc, player)
                flipped.append((fr, fc, opponent))
        
        message = f"{player.name} moves to ({row + 1}, {col + 1}), flipped {len(flipped)} stones."
        return MoveDelta(
            row=row, col=col, player=player,
            captured=flipped,
            message=message, pre_state=pre_state
        )

    def _post_move(self, delta: MoveDelta) -> None:
        """落子后检查游戏是否结束。"""
        self.pass_count = 0
        
        if self._is_board_full():
            self._finalize_score()

    def undo_move(self, delta: MoveDelta) -> None:
        """悔棋：恢复落子位置和翻转的棋子。"""
        self.board.set(delta.row, delta.col, Stone.EMPTY)
        for r, c, original_color in delta.captured:
            self.board.set(r, c, original_color)
        self.restore_state(delta.pre_state)

    def execute_pass(self) -> PassRecord:
        """执行 pass（黑白棋只有无合法落子时才能 pass）。"""
        if self.is_over:
            raise GameError("Game already ended.")
        
        if not self.must_pass():
            raise GameError("You have legal moves, cannot pass.")
        
        record = PassRecord(
            player=self.current_player,
            message=f"{self.current_player.name} has no legal moves, passes.",
            pre_state=self.record_state()
        )
        self.pass_count += 1
        self.switch_player()
        
        # 检查对手是否也无法落子
        if self.must_pass():
            self._finalize_score()
        
        return record

    def undo_pass(self, record: PassRecord) -> None:
        """撤销 pass。"""
        self.restore_state(record.pre_state)

    def get_legal_moves(self) -> List[Tuple[int, int]]:
        """获取当前玩家所有合法落子位置。"""
        if self.is_over:
            return []
        legal = []
        for r in range(self.board.size):
            for c in range(self.board.size):
                if self.is_legal_move(r, c, self.current_player):
                    legal.append((r, c))
        return legal

    def must_pass(self) -> bool:
        """当前玩家是否必须 pass（无合法落子）。"""
        return len(self.get_legal_moves()) == 0 and not self.is_over

    def _is_board_full(self) -> bool:
        """棋盘是否填满。"""
        for r in range(self.board.size):
            for c in range(self.board.size):
                if self.board.is_empty(r, c):
                    return False
        return True

    def _finalize_score(self) -> None:
        """计算最终得分，判定胜负。"""
        black_count = self.board.count_stones(Stone.BLACK)
        white_count = self.board.count_stones(Stone.WHITE)
        
        if black_count > white_count:
            self.winner = Stone.BLACK
        elif white_count > black_count:
            self.winner = Stone.WHITE
        else:
            self.winner = None
        
        self.is_over = True
