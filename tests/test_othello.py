"""黑白棋测试用例。"""
import pytest
from core.board import Stone
from core.game import GameError
from core.othello import OthelloGame


class TestOthelloBasic:
    """黑白棋基本功能测试。"""

    def test_initial_setup(self):
        """测试初始局面设置。"""
        game = OthelloGame(8)
        # 检查中央 4 子
        assert game.board.get(3, 3) == Stone.WHITE
        assert game.board.get(3, 4) == Stone.BLACK
        assert game.board.get(4, 3) == Stone.BLACK
        assert game.board.get(4, 4) == Stone.WHITE
        # 黑方先手
        assert game.current_player == Stone.BLACK

    def test_legal_moves_initial(self):
        """测试初始局面的合法落子。"""
        game = OthelloGame(8)
        legal = game.get_legal_moves()
        # 初始局面黑方有 4 个合法位置
        expected = [(2, 3), (3, 2), (4, 5), (5, 4)]
        assert sorted(legal) == sorted(expected)


class TestOthelloMove:
    """黑白棋落子测试。"""

    def test_legal_move_basic(self):
        """测试基本合法落子。"""
        game = OthelloGame(8)
        delta = game.execute_move(2, 3)
        
        assert game.board.get(2, 3) == Stone.BLACK
        assert game.board.get(3, 3) == Stone.BLACK  # 被翻转
        assert len(delta.captured) == 1
        assert delta.captured[0] == (3, 3, Stone.WHITE)

    def test_illegal_move_no_flip(self):
        """测试非法落子（不能翻转）。"""
        game = OthelloGame(8)
        with pytest.raises(GameError, match="Illegal move"):
            game.execute_move(0, 0)

    def test_illegal_move_occupied(self):
        """测试非法落子（已被占用）。"""
        game = OthelloGame(8)
        with pytest.raises(GameError, match="Illegal move"):
            game.execute_move(3, 3)

    def test_flip_multiple_directions(self):
        """测试多方向翻转。"""
        game = OthelloGame(8)
        # 构造特定局面
        game.execute_move(2, 3)  # 黑
        game.execute_move(2, 2)  # 白
        game.execute_move(2, 1)  # 黑 - 应该翻转 (2,2)
        
        assert game.board.get(2, 1) == Stone.BLACK
        assert game.board.get(2, 2) == Stone.BLACK


class TestOthelloPass:
    """黑白棋 pass 测试。"""

    def test_cannot_pass_with_legal_moves(self):
        """测试有合法落子时不能 pass。"""
        game = OthelloGame(8)
        with pytest.raises(GameError, match="have legal moves"):
            game.execute_pass()

    def test_must_pass(self):
        """测试 must_pass 判断。"""
        game = OthelloGame(8)
        assert not game.must_pass()


class TestOthelloGameOver:
    """黑白棋终局测试。"""

    def test_game_over_by_score(self):
        """测试按子数判定胜负。"""
        game = OthelloGame(8)
        game.board.clear()
        
        # 黑 40 子
        for r in range(5):
            for c in range(8):
                game.board.set(r, c, Stone.BLACK)
        # 白 24 子
        for r in range(5, 8):
            for c in range(8):
                game.board.set(r, c, Stone.WHITE)
        
        game._finalize_score()
        
        assert game.is_over
        assert game.winner == Stone.BLACK


class TestOthelloUndo:
    """黑白棋悔棋测试。"""

    def test_undo_move(self):
        """测试悔棋恢复。"""
        game = OthelloGame(8)
        initial_snapshot = game.board.snapshot()
        
        delta = game.execute_move(2, 3)
        game.undo_move(delta)
        
        assert game.board.snapshot() == initial_snapshot
        assert game.current_player == Stone.BLACK


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
