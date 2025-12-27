"""快速测试脚本。"""
import sys
sys.path.insert(0, '.')

from core.othello import OthelloGame
from core.board import Stone
from core.game import GameError

print("Running basic tests...")

# 测试 1: 初始局面
game = OthelloGame(8)
assert game.board.get(3, 3) == Stone.WHITE
assert game.board.get(3, 4) == Stone.BLACK
print('Test 1 passed: Initial setup')

# 测试 2: 合法落子
game = OthelloGame(8)
delta = game.execute_move(2, 3)
assert game.board.get(2, 3) == Stone.BLACK
assert game.board.get(3, 3) == Stone.BLACK
print('Test 2 passed: Legal move')

# 测试 3: 非法落子
game = OthelloGame(8)
try:
    game.execute_move(0, 0)
    assert False, 'Should raise error'
except GameError:
    pass
print('Test 3 passed: Illegal move rejected')

# 测试 4: 悔棋
game = OthelloGame(8)
snapshot = game.board.snapshot()
delta = game.execute_move(2, 3)
game.undo_move(delta)
assert game.board.snapshot() == snapshot
print('Test 4 passed: Undo move')

# 测试 5: AI 对战
from player.ai.eval_ai import OthelloEvalStrategy
from player.ai.random_ai import RandomStrategy

game = OthelloGame(8)
eval_ai = OthelloEvalStrategy()
random_ai = RandomStrategy()

for _ in range(5):
    if game.is_over:
        break
    legal = game.get_legal_moves()
    if not legal:
        break
    if game.current_player == Stone.BLACK:
        row, col = eval_ai.select_move(game)
    else:
        row, col = random_ai.select_move(game)
    game.execute_move(row, col)
print('Test 5 passed: AI moves')

# 测试 6: 账户系统
from account.hasher import PasswordHasher
password = 'test123'
hashed = PasswordHasher.hash_password(password)
assert PasswordHasher.verify_password(password, hashed)
assert not PasswordHasher.verify_password('wrong', hashed)
print('Test 6 passed: Password hashing')

# 测试 7: 录像
from match.recorder import GameRecorder
from player.base import PlayerAction

game = OthelloGame(8)
recorder = GameRecorder('othello', 8, 'Alice', 'Bob')
recorder.set_initial_board(game.board.snapshot())
action = PlayerAction.move(2, 3)
recorder.record_move(action, Stone.BLACK, game.board.snapshot())
data = recorder.export()
assert len(data['moves']) == 1
print('Test 7 passed: Recording')

# 测试 8: 回放
from replay.controller import ReplayController
ctrl = ReplayController()
ctrl.load(data)
assert ctrl.get_total_moves() == 1
print('Test 8 passed: Replay')

print()
print('=' * 40)
print('All 8 tests passed!')
print('=' * 40)
