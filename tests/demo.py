"""Lightweight demo helpers (manual run)."""
from core.game import MoveCommand, PassCommand
from core.gomoku import GomokuGame
from core.go import GoGame


def demo_gomoku_win() -> None:
    game = GomokuGame(8)
    moves = [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (0, 3), (1, 3), (0, 4)]
    for col, row in moves:
        cmd = MoveCommand(game, row, col)
        print(cmd.execute())
        game.add_history(cmd)
        if game.is_over:
            break
    print(f"Winner expected: BLACK, actual: {game.winner}")


def demo_go_capture() -> None:
    game = GoGame(8)
    # Simple capture shape
    seq = [
        (3, 3),  # B
        (3, 4),  # W
        (4, 3),  # B
        (2, 4),  # W
        (4, 4),  # B
        (2, 3),  # W
        (3, 2),  # B
    ]
    for idx, (col, row) in enumerate(seq):
        cmd = MoveCommand(game, row, col)
        print(cmd.execute())
        game.add_history(cmd)
        if idx == 5:
            print("White stone at (3,4) should be in atari.")
    # Final move to capture
    cmd = MoveCommand(game, 3, 4)  # White attempts suicide should fail
    try:
        cmd.execute()
    except Exception as exc:  # pragma: no cover - demonstration only
        print(f"Expected error: {exc}")

    pass_cmd = PassCommand(game)
    print(pass_cmd.execute())
    game.add_history(pass_cmd)


if __name__ == "__main__":
    demo_gomoku_win()
    print("-" * 30)
    demo_go_capture()
