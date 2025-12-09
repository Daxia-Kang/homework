"""Console UI for the board platform."""
from __future__ import annotations

from typing import Optional

from core.board import Stone
from core.game import (
    Command,
    Game,
    GameError,
    GameFactory,
    MoveCommand,
    PassCommand,
    ResignCommand,
)
from storage.save_load import load_game, save_game


class BoardRenderer:
    """Responsible for rendering the board on console."""

    @staticmethod
    def render(game: Game) -> str:
        size = game.board.size
        header = "   " + " ".join(f"{i:2d}" for i in range(1, size + 1))
        lines = [header]
        for idx, row in enumerate(game.board.grid, start=1):
            line = f"{idx:2d} " + " ".join(BoardRenderer._symbol(cell) for cell in row)
            lines.append(line)
        lines.append(f"Turn: {game.current_player.name}")
        if game.is_over:
            result = (
                f"Winner: {game.winner.name}"
                if game.winner
                else "Result: Draw (no winner)"
            )
            lines.append(result)
        return "\n".join(lines)

    @staticmethod
    def _symbol(cell: Stone) -> str:
        if cell == Stone.BLACK:
            return "B"
        if cell == Stone.WHITE:
            return "W"
        return "."


class ConsoleUI:
    def __init__(self) -> None:
        self.game: Optional[Game] = None
        self.help_visible = True
        self.last_game_type: Optional[str] = None
        self.last_size: Optional[int] = None

    def run(self) -> None:
        print("Board Platform (Gomoku & Go) - type 'help' for instructions.")
        while True:
            if self.help_visible:
                self.print_help_short()
            try:
                raw = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye.")
                return
            if not raw:
                continue
            parts = raw.split()
            cmd = parts[0].lower()
            args = parts[1:]

            try:
                if cmd == "start":
                    self.handle_start(args)
                elif cmd == "restart":
                    self.handle_restart(args)
                elif cmd == "move":
                    self.handle_move(args)
                elif cmd == "pass":
                    self.handle_pass()
                elif cmd == "undo":
                    self.handle_undo()
                elif cmd == "resign":
                    self.handle_resign()
                elif cmd == "save":
                    self.handle_save(args)
                elif cmd == "load":
                    self.handle_load(args)
                elif cmd == "help":
                    self.print_help_full()
                elif cmd == "hide_help":
                    self.help_visible = False
                elif cmd == "show_help":
                    self.help_visible = True
                elif cmd in {"quit", "exit"}:
                    print("Goodbye.")
                    return
                else:
                    print("Unknown command. Type 'help' for options.")
            except GameError as exc:
                print(f"[Error] {exc}")
            except ValueError as exc:
                print(f"[Error] {exc}")

            if self.game:
                print(BoardRenderer.render(self.game))

    def handle_start(self, args: list[str]) -> None:
        game_type, size = self._parse_game_options(args)
        self.game = GameFactory.create(game_type, size)
        self.game.history.clear()
        self.last_game_type = game_type
        self.last_size = size
        print(f"Started {game_type} on {size}x{size} board.")

    def handle_restart(self, args: list[str]) -> None:
        if not args and self.last_game_type and self.last_size:
            self.handle_start([self.last_game_type, str(self.last_size)])
            return
        self.handle_start(args)

    def handle_move(self, args: list[str]) -> None:
        self._ensure_game()
        if len(args) != 2:
            raise ValueError("Usage: move x y (1-based coordinates).")
        row = int(args[1]) - 1
        col = int(args[0]) - 1
        command = MoveCommand(self.game, row, col)  # type: ignore[arg-type]
        message = command.execute()
        self.game.add_history(command)  # type: ignore[arg-type]
        print(message)
        if self.game.is_over:
            print("Game ended.")

    def handle_pass(self) -> None:
        self._ensure_game()
        command: Command = PassCommand(self.game)  # type: ignore[arg-type]
        message = command.execute()
        self.game.add_history(command)
        print(message)
        if self.game.is_over:
            print("Both players passed. Game ended.")

    def handle_undo(self) -> None:
        self._ensure_game()
        last = self.game.pop_history()
        if not last:
            print("No moves to undo.")
            return
        msg = last.undo()
        print(msg)

    def handle_resign(self) -> None:
        self._ensure_game()
        command: Command = ResignCommand(self.game)  # type: ignore[arg-type]
        message = command.execute()
        self.game.add_history(command)
        print(message)

    def handle_save(self, args: list[str]) -> None:
        self._ensure_game()
        if len(args) != 1:
            raise ValueError("Usage: save filename.json")
        save_game(self.game, args[0])
        print(f"Saved to {args[0]}")

    def handle_load(self, args: list[str]) -> None:
        if len(args) != 1:
            raise ValueError("Usage: load filename.json")
        self.game = load_game(args[0])
        self.last_game_type = self.game.name.lower()
        self.last_size = self.game.board.size
        print(f"Loaded {self.game.name} from {args[0]}")

    def _parse_game_options(self, args: list[str]) -> tuple[str, int]:
        if len(args) >= 1:
            game_type = args[0].lower()
        else:
            game_type = input("Choose game (gomoku/go): ").strip().lower()
        if game_type not in {"gomoku", "go"}:
            raise ValueError("Game type must be 'gomoku' or 'go'.")

        if len(args) >= 2:
            size = int(args[1])
        else:
            size = int(input("Board size (8-19): ").strip())
        if size < 8 or size > 19:
            raise ValueError("Board size must be between 8 and 19.")
        return game_type, size

    def _ensure_game(self) -> None:
        if not self.game:
            raise GameError("Start or load a game first.")

    def print_help_short(self) -> None:
        print("Commands: start, move x y, pass (Go), undo, resign, save, load, restart, help, exit")

    def print_help_full(self) -> None:
        print(
            "help: show this message\n"
            "start [gomoku|go] [size]: start a new game (8-19)\n"
            "move x y: place a stone at column x, row y (1-based)\n"
            "pass: skip a turn (Go only)\n"
            "undo: revert last action\n"
            "resign: current player resigns\n"
            "save <file>: save current game\n"
            "load <file>: load a saved game\n"
            "restart: restart using last settings or provide new\n"
            "hide_help/show_help: toggle short help banner\n"
            "exit/quit: leave the program"
        )
