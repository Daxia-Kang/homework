"""Evaluation-based AI strategy - 二级评分 AI。

使用评分函数评估每个合法位置，选择得分最高的位置。
针对不同游戏类型提供不同的评分策略。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple, Optional

from core.board import Stone
from player.base import IPlayer, PlayerType, PlayerAction, ActionType, GameResult
from player.ai.base import IAI, IMoveStrategy, AIDifficulty
from player.ai.random_ai import RandomStrategy

if TYPE_CHECKING:
    from core.game import Game


class OthelloEvalStrategy(IMoveStrategy):
    """黑白棋评分策略。
    
    评分因素：
    1. 位置权重（角落最高，X/C 格最危险）
    2. 行动力（可选位置数量）
    3. 稳定子（不会被翻转的棋子）
    4. 翻转数量
    """

    # 8x8 棋盘位置权重矩阵
    # 角落(100)最重要，X格(-50)和C格(-20)危险
    POSITION_WEIGHTS_8x8 = [
        [100, -20,  10,   5,   5,  10, -20, 100],
        [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
        [ 10,  -2,   1,   1,   1,   1,  -2,  10],
        [  5,  -2,   1,   0,   0,   1,  -2,   5],
        [  5,  -2,   1,   0,   0,   1,  -2,   5],
        [ 10,  -2,   1,   1,   1,   1,  -2,  10],
        [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
        [100, -20,  10,   5,   5,  10, -20, 100],
    ]

    # 权重系数
    WEIGHT_POSITION = 10.0
    WEIGHT_MOBILITY = 5.0
    WEIGHT_FLIP_COUNT = 2.0
    WEIGHT_CORNER_PROXIMITY = 15.0

    def select_move(self, game: "Game") -> Tuple[int, int]:
        """选择评分最高的落子位置。"""
        legal_moves = game.get_legal_moves()
        if not legal_moves:
            raise ValueError("No legal moves available")

        player = game.current_player
        best_move: Optional[Tuple[int, int]] = None
        best_score = float('-inf')

        for row, col in legal_moves:
            score = self._evaluate_move(game, row, col, player)
            if score > best_score:
                best_score = score
                best_move = (row, col)

        return best_move if best_move else legal_moves[0]

    def _evaluate_move(self, game: "Game", row: int, col: int, player: Stone) -> float:
        """评估在 (row, col) 落子的价值。"""
        score = 0.0

        # 1. 位置分数
        score += self._position_score(game, row, col) * self.WEIGHT_POSITION

        # 2. 模拟落子后的行动力
        game_copy = game.clone()
        try:
            delta = game_copy.execute_move(row, col)
            # 翻转数量奖励
            score += len(delta.captured) * self.WEIGHT_FLIP_COUNT
            
            # 对手行动力惩罚（我们希望对手选择少）
            opponent_moves = len(game_copy.get_legal_moves())
            score -= opponent_moves * self.WEIGHT_MOBILITY
        except Exception:
            pass

        # 3. 角落邻近惩罚/奖励
        score += self._corner_proximity_score(game, row, col, player) * self.WEIGHT_CORNER_PROXIMITY

        return score

    def _position_score(self, game: "Game", row: int, col: int) -> float:
        """获取位置权重分数。"""
        size = game.board.size
        if size == 8:
            return float(self.POSITION_WEIGHTS_8x8[row][col])
        
        # 非标准棋盘：简化处理，角落高分
        corners = [(0, 0), (0, size-1), (size-1, 0), (size-1, size-1)]
        if (row, col) in corners:
            return 100.0
        
        # 边缘中等分
        if row == 0 or row == size-1 or col == 0 or col == size-1:
            return 5.0
        
        return 0.0

    def _corner_proximity_score(self, game: "Game", row: int, col: int, player: Stone) -> float:
        """角落邻近评分。
        
        如果角落已被占据，邻近位置变得安全；
        如果角落为空，邻近位置（X/C格）危险。
        """
        size = game.board.size
        corners = [(0, 0), (0, size-1), (size-1, 0), (size-1, size-1)]
        x_squares = [(1, 1), (1, size-2), (size-2, 1), (size-2, size-2)]
        
        score = 0.0
        
        # 如果落在 X 格，检查对应角落
        if (row, col) in x_squares:
            idx = x_squares.index((row, col))
            corner = corners[idx]
            if game.board.is_empty(corner[0], corner[1]):
                score -= 25.0  # 角落为空时，X格危险
            else:
                score += 5.0   # 角落已占，X格安全
        
        # 落在角落是最好的
        if (row, col) in corners:
            score += 50.0
        
        return score

    @property
    def name(self) -> str:
        return "OthelloEval"


class GomokuEvalStrategy(IMoveStrategy):
    """五子棋评分策略。
    
    评分因素：
    1. 进攻：形成连子的潜力
    2. 防守：阻止对手连子
    """

    # 棋型分数
    PATTERN_SCORES = {
        5: 100000,    # 连五
        4: 10000,     # 活四
        3: 1000,      # 活三
        2: 100,       # 活二
        1: 10,        # 单子
    }

    def select_move(self, game: "Game") -> Tuple[int, int]:
        """选择评分最高的落子位置。"""
        legal_moves = game.get_legal_moves()
        if not legal_moves:
            raise ValueError("No legal moves available")

        player = game.current_player
        opponent = player.opposite()
        best_move: Optional[Tuple[int, int]] = None
        best_score = float('-inf')

        for row, col in legal_moves:
            # 进攻分数
            attack_score = self._evaluate_position(game, row, col, player)
            # 防守分数（阻止对手）
            defense_score = self._evaluate_position(game, row, col, opponent)
            
            total_score = attack_score + defense_score * 0.9
            
            if total_score > best_score:
                best_score = total_score
                best_move = (row, col)

        return best_move if best_move else legal_moves[0]

    def _evaluate_position(self, game: "Game", row: int, col: int, player: Stone) -> float:
        """评估在 (row, col) 落子对 player 的价值。"""
        score = 0.0
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count, open_ends = self._count_line(game, row, col, dr, dc, player)
            score += self._score_pattern(count, open_ends)
        
        return score

    def _count_line(self, game: "Game", row: int, col: int,
                    dr: int, dc: int, player: Stone) -> Tuple[int, int]:
        """计算某方向上的连子数和开放端数。"""
        count = 1
        open_ends = 0
        
        # 正方向
        r, c = row + dr, col + dc
        while game.board.is_on_board(r, c) and game.board.get(r, c) == player:
            count += 1
            r += dr
            c += dc
        if game.board.is_on_board(r, c) and game.board.is_empty(r, c):
            open_ends += 1
        
        # 反方向
        r, c = row - dr, col - dc
        while game.board.is_on_board(r, c) and game.board.get(r, c) == player:
            count += 1
            r -= dr
            c -= dc
        if game.board.is_on_board(r, c) and game.board.is_empty(r, c):
            open_ends += 1
        
        return count, open_ends

    def _score_pattern(self, count: int, open_ends: int) -> float:
        """根据连子数和开放端数计算分数。"""
        if count >= 5:
            return self.PATTERN_SCORES[5]
        
        if open_ends == 0:
            return 0  # 两端都被堵，无价值
        
        base_score = self.PATTERN_SCORES.get(count, 0)
        
        # 活棋（两端开放）价值更高
        if open_ends == 2:
            return base_score * 2
        return base_score

    @property
    def name(self) -> str:
        return "GomokuEval"


class AIPlayer(IPlayer, IAI):
    """AI 玩家实现。
    
    设计模式：策略模式
    - 持有 IMoveStrategy 策略对象
    - 通过策略对象选择落子位置
    - 可运行时切换策略
    """

    def __init__(
        self,
        name: str,
        strategy: IMoveStrategy,
        difficulty: AIDifficulty = AIDifficulty.EASY
    ) -> None:
        """初始化 AI 玩家。
        
        Args:
            name: AI 名称
            strategy: 落子策略
            difficulty: 难度等级
        """
        self._name = name
        self._strategy = strategy
        self._difficulty = difficulty
        self._player_type = PlayerType.AI

    @property
    def name(self) -> str:
        return self._name

    @property
    def player_type(self) -> PlayerType:
        return self._player_type

    @property
    def difficulty(self) -> AIDifficulty:
        return self._difficulty

    def get_action(self, game: "Game") -> PlayerAction:
        """获取 AI 的下一步动作。"""
        # 检查是否必须 pass
        if game.must_pass():
            return PlayerAction.pass_turn()
        
        # 使用策略选择落子
        row, col = self._strategy.select_move(game)
        return PlayerAction.move(row, col)

    def select_move(self, game: "Game") -> Tuple[int, int]:
        """直接选择落子位置（IAI 接口）。"""
        return self._strategy.select_move(game)

    def notify_result(self, result: GameResult) -> None:
        """AI 不需要处理结果通知。"""
        pass

    def set_strategy(self, strategy: IMoveStrategy) -> None:
        """切换落子策略。"""
        self._strategy = strategy


class EvalStrategyFactory:
    """评分策略工厂。
    
    根据游戏类型创建对应的评分策略。
    """

    @staticmethod
    def create(game_type: str) -> IMoveStrategy:
        """根据游戏类型创建评分策略。
        
        Args:
            game_type: 游戏类型（gomoku/othello/go）
            
        Returns:
            对应的评分策略
        """
        game_type = game_type.lower()
        if game_type == "othello":
            return OthelloEvalStrategy()
        if game_type == "gomoku":
            return GomokuEvalStrategy()
        # 默认使用随机策略
        return RandomStrategy()


def create_ai_player(difficulty: AIDifficulty, game_type: str) -> AIPlayer:
    """创建指定难度的 AI 玩家。
    
    Args:
        difficulty: AI 难度
        game_type: 游戏类型
        
    Returns:
        AI 玩家实例
    """
    if difficulty == AIDifficulty.EASY:
        strategy = RandomStrategy()
        name = "AI-Easy"
    elif difficulty == AIDifficulty.MEDIUM:
        strategy = EvalStrategyFactory.create(game_type)
        name = "AI-Medium"
    else:
        # HARD 级别暂用评分策略
        strategy = EvalStrategyFactory.create(game_type)
        name = "AI-Hard"
    
    return AIPlayer(name, strategy, difficulty)
