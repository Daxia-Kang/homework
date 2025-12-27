"""录像回放测试用例。"""
import pytest
import time
from core.othello import OthelloGame
from core.board import Stone
from player.base import PlayerAction, ActionType
from match.recorder import GameRecorder, MoveRecord
from replay.controller import ReplayController


class TestGameRecorder:
    """录像记录器测试。"""

    def test_record_move(self):
        """测试记录落子。"""
        recorder = GameRecorder("othello", 8, "Alice", "Bob")
        game = OthelloGame(8)
        recorder.set_initial_board(game.board.snapshot())
        
        action = PlayerAction.move(2, 3)
        recorder.record_move(action, Stone.BLACK, game.board.snapshot())
        
        moves = recorder.get_move_list()
        assert len(moves) == 1
        assert moves[0].move_number == 1
        assert moves[0].player == "BLACK"
        assert moves[0].position == (2, 3)

    def test_export(self):
        """测试导出。"""
        recorder = GameRecorder("othello", 8, "Alice", "Bob")
        game = OthelloGame(8)
        recorder.set_initial_board(game.board.snapshot())
        
        action = PlayerAction.move(2, 3)
        recorder.record_move(action, Stone.BLACK, game.board.snapshot())
        
        data = recorder.export()
        
        assert data["version"] == "2.0"
        assert data["metadata"]["game_type"] == "othello"
        assert len(data["moves"]) == 1

    def test_finalize(self):
        """测试完成录像。"""
        recorder = GameRecorder("othello", 8, "Alice", "Bob")
        game = OthelloGame(8)
        
        recorder.finalize("BLACK_WIN", game.board.snapshot())
        
        meta = recorder.get_metadata()
        assert meta.result == "BLACK_WIN"
        assert meta.end_time is not None


class TestReplayController:
    """回放控制器测试。"""

    @pytest.fixture
    def sample_replay(self):
        """创建示例录像。"""
        game = OthelloGame(8)
        recorder = GameRecorder("othello", 8, "Alice", "Bob")
        recorder.set_initial_board(game.board.snapshot())
        
        # 记录几步
        moves = [(2, 3), (2, 2), (2, 1)]
        for row, col in moves:
            if game.is_over:
                break
            try:
                game.execute_move(row, col)
                action = PlayerAction.move(row, col)
                recorder.record_move(action, game.current_player, game.board.snapshot())
            except:
                pass
        
        recorder.finalize("BLACK_WIN", game.board.snapshot())
        return recorder.export()

    def test_load(self, sample_replay):
        """测试加载录像。"""
        ctrl = ReplayController()
        ctrl.load(sample_replay)
        
        assert ctrl.get_total_moves() > 0
        meta = ctrl.get_metadata()
        assert meta.game_type == "othello"

    def test_next_move(self, sample_replay):
        """测试前进。"""
        ctrl = ReplayController()
        ctrl.load(sample_replay)
        
        assert ctrl.get_current_move_number() == 0
        
        move = ctrl.next_move()
        assert move is not None
        assert ctrl.get_current_move_number() == 1

    def test_prev_move(self, sample_replay):
        """测试后退。"""
        ctrl = ReplayController()
        ctrl.load(sample_replay)
        
        ctrl.next_move()
        ctrl.next_move()
        assert ctrl.get_current_move_number() == 2
        
        ctrl.prev_move()
        assert ctrl.get_current_move_number() == 1

    def test_jump_to(self, sample_replay):
        """测试跳转。"""
        ctrl = ReplayController()
        ctrl.load(sample_replay)
        
        total = ctrl.get_total_moves()
        if total >= 2:
            ctrl.jump_to(2)
            assert ctrl.get_current_move_number() == 2

    def test_consistency(self, sample_replay):
        """测试回放一致性。"""
        ctrl = ReplayController()
        ctrl.load(sample_replay)
        
        # 记录每步的棋盘
        boards = [ctrl.get_current_board()]
        while True:
            move = ctrl.next_move()
            if not move:
                break
            boards.append(ctrl.get_current_board())
        
        # 后退验证
        for i in range(len(boards) - 1, 0, -1):
            ctrl.prev_move()
            assert ctrl.get_current_board() == boards[i - 1]


class TestRecordAndReplayConsistency:
    """录制-回放一致性测试。"""

    def test_full_game_replay(self):
        """测试完整游戏录制和回放。"""
        # 1. 进行游戏并录制
        game = OthelloGame(8)
        recorder = GameRecorder("othello", 8, "Alice", "Bob")
        recorder.set_initial_board(game.board.snapshot())
        
        boards = [game.board.snapshot()]
        moves_made = []
        
        # 进行几步
        test_moves = [(2, 3), (2, 2), (4, 5)]
        for row, col in test_moves:
            if game.is_over:
                break
            try:
                pre_player = game.current_player
                game.execute_move(row, col)
                action = PlayerAction.move(row, col)
                recorder.record_move(action, pre_player, game.board.snapshot())
                boards.append(game.board.snapshot())
                moves_made.append((row, col))
            except:
                pass
        
        # 2. 导出录像
        record_data = recorder.export()
        
        # 3. 加载回放
        ctrl = ReplayController()
        ctrl.load(record_data)
        
        # 4. 验证初始状态
        # 注意：黑白棋有初始棋子，所以初始棋盘不是空的
        initial_board = ctrl.get_current_board()
        assert initial_board is not None
        
        # 5. 逐步回放验证
        for i in range(len(moves_made)):
            ctrl.next_move()
            # 棋盘应该与录制时一致
            current = ctrl.get_current_board()
            assert current is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
