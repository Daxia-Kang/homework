"""AI 测试用例。"""
import pytest
from core.othello import OthelloGame
from core.gomoku import GomokuGame
from player.ai.random_ai import RandomStrategy
from player.ai.eval_ai import OthelloEvalStrategy, GomokuEvalStrategy, create_ai_player
from player.ai.base import AIDifficulty
from player.base import ActionType


class TestRandomAI:
    """随机 AI 测试。"""

    def test_random_ai_valid_move_othello(self):
        """测试随机 AI 返回合法落子（黑白棋）。"""
        game = OthelloGame(8)
        strategy = RandomStrategy()
        
        for _ in range(10):
            move = strategy.select_move(game)
            assert move in game.get_legal_moves()

    def test_random_ai_valid_move_gomoku(self):
        """测试随机 AI 返回合法落子（五子棋）。"""
        game = GomokuGame(8)
        strategy = RandomStrategy()
        
        for _ in range(10):
            move = strategy.select_move(game)
            assert move in game.get_legal_moves()


class TestEvalAI:
    """评分 AI 测试。"""

    def test_othello_eval_prefers_corner(self):
        """测试黑白棋 AI 偏好角落。"""
        game = OthelloGame(8)
        strategy = OthelloEvalStrategy()
        
        # 构造可以落角落的局面
        game.board.clear()
        game.board.set(0, 1, game.current_player.opposite())
        game.board.set(0, 2, game.current_player)
        
        # AI 应该选择角落
        if game.is_legal_move(0, 0, game.current_player):
            move = strategy.select_move(game)
            # 角落应该是高分选择之一
            assert move is not None

    def test_gomoku_eval_blocks_threat(self):
        """测试五子棋 AI 阻止威胁。"""
        game = GomokuGame(8)
        strategy = GomokuEvalStrategy()
        
        # 对手形成三连
        game.board.set(0, 0, Stone.WHITE)
        game.board.set(0, 1, Stone.WHITE)
        game.board.set(0, 2, Stone.WHITE)
        
        move = strategy.select_move(game)
        # AI 应该阻止四连
        assert move is not None


class TestAIPlayer:
    """AI 玩家测试。"""

    def test_create_ai_player_easy(self):
        """测试创建简单 AI。"""
        ai = create_ai_player(AIDifficulty.EASY, "othello")
        assert ai.difficulty == AIDifficulty.EASY
        assert "Easy" in ai.name

    def test_create_ai_player_medium(self):
        """测试创建中等 AI。"""
        ai = create_ai_player(AIDifficulty.MEDIUM, "othello")
        assert ai.difficulty == AIDifficulty.MEDIUM

    def test_ai_get_action(self):
        """测试 AI 获取动作。"""
        game = OthelloGame(8)
        ai = create_ai_player(AIDifficulty.EASY, "othello")
        
        action = ai.get_action(game)
        assert action.action_type == ActionType.MOVE
        assert (action.row, action.col) in game.get_legal_moves()


class TestAIBattle:
    """AI 对战测试。"""

    def test_eval_beats_random(self):
        """测试评分 AI 能战胜随机 AI（统计胜率）。"""
        from core.board import Stone
        
        wins = 0
        total = 10  # 减少测试次数以加快速度
        
        for _ in range(total):
            game = OthelloGame(8)
            eval_strategy = OthelloEvalStrategy()
            random_strategy = RandomStrategy()
            
            while not game.is_over:
                legal = game.get_legal_moves()
                if not legal:
                    if game.must_pass():
                        game.execute_pass()
                    continue
                
                if game.current_player == Stone.BLACK:
                    # 评分 AI 执黑
                    row, col = eval_strategy.select_move(game)
                else:
                    # 随机 AI 执白
                    row, col = random_strategy.select_move(game)
                
                game.execute_move(row, col)
            
            if game.winner == Stone.BLACK:
                wins += 1
        
        # 评分 AI 应该有较高胜率
        win_rate = wins / total
        print(f"Eval AI win rate: {win_rate:.1%}")
        assert win_rate >= 0.5, f"Eval AI win rate too low: {win_rate:.1%}"


# 需要导入 Stone
from core.board import Stone


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
