"""Console UI for the board platform.

扩展功能：
1. 支持黑白棋
2. 支持 AI 对战
3. 支持账户登录/注册
4. 支持录像回放
"""
from __future__ import annotations

from typing import Optional, Callable

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
from storage.save_load import load_game, save_game, load_replay, save_replay
from player.base import IPlayer, PlayerAction, ActionType, PlayerType
from player.human import HumanPlayer, GuestPlayer
from player.ai.base import AIDifficulty
from player.ai.eval_ai import create_ai_player
from match.controller import MatchController
from match.recorder import GameRecorder
from account.service import AccountService
from replay.controller import ReplayController


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
            return " B"
        if cell == Stone.WHITE:
            return " W"
        return " ."


class ConsoleUI:
    """命令行交互界面。
    
    支持功能：
    - 基础对战（五子棋/围棋/黑白棋）
    - AI 对战
    - 账户登录/注册
    - 录像回放
    """

    def __init__(self) -> None:
        self.game: Optional[Game] = None
        self.match: Optional[MatchController] = None
        self.help_visible = True
        self.last_game_type: Optional[str] = None
        self.last_size: Optional[int] = None
        self.account_service = AccountService()
        self.replay_controller: Optional[ReplayController] = None
        self.in_replay_mode = False
        
        # AI 对战相关
        self.black_player: Optional[IPlayer] = None
        self.white_player: Optional[IPlayer] = None
        self.ai_mode = False

    def run(self) -> None:
        print("=" * 60)
        print("  棋类对战平台 v2.0")
        print("  支持: 五子棋(gomoku) | 围棋(go) | 黑白棋(othello)")
        print("=" * 60)
        print("输入 'help' 查看完整帮助")
        
        while True:
            if self.help_visible and not self.in_replay_mode:
                self.print_help_short()
            
            try:
                prompt = self._get_prompt()
                raw = input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye.")
                return
            
            if not raw:
                continue
            
            parts = raw.split()
            cmd = parts[0].lower()
            args = parts[1:]

            try:
                # 回放模式命令
                if self.in_replay_mode:
                    if not self._handle_replay_command(cmd, args):
                        continue
                    continue
                
                # 普通模式命令
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
                elif cmd == "ai":
                    self.handle_ai_game(args)
                elif cmd == "login":
                    self.handle_login()
                elif cmd == "register":
                    self.handle_register()
                elif cmd == "logout":
                    self.handle_logout()
                elif cmd == "status":
                    self.handle_status()
                elif cmd == "replay":
                    self.handle_replay(args)
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

            if self.game and not self.in_replay_mode:
                print(BoardRenderer.render(self.game))
                
                # AI 自动落子
                if self.ai_mode and not self.game.is_over:
                    self._ai_turn()

    def _get_prompt(self) -> str:
        """获取命令提示符。"""
        if self.in_replay_mode:
            ctrl = self.replay_controller
            return f"[回放 {ctrl.get_current_move_number()}/{ctrl.get_total_moves()}] > "
        
        user = self.account_service.get_current_user()
        if user:
            return f"[{user.username}] > "
        return "[游客] > "

    # ==================== 游戏控制 ====================

    def handle_start(self, args: list[str]) -> None:
        """开始新游戏。"""
        game_type, size = self._parse_game_options(args)
        self.game = GameFactory.create(game_type, size)
        self.game.history.clear()
        self.last_game_type = game_type
        self.last_size = size
        self.ai_mode = False
        
        # 创建录像记录器
        user = self.account_service.get_current_user()
        self.match = MatchController()
        self.black_player = GuestPlayer() if not user else HumanPlayer(user.username, user=user)
        self.white_player = GuestPlayer() if not user else HumanPlayer(user.username, user=user)
        self.match.start(game_type, size, self.black_player, self.white_player,
                        user.user_id if user else None)
        
        print(f"Started {game_type} on {size}x{size} board.")

    def handle_restart(self, args: list[str]) -> None:
        """重新开始游戏。"""
        if not args and self.last_game_type and self.last_size:
            self.handle_start([self.last_game_type, str(self.last_size)])
            return
        self.handle_start(args)

    def handle_move(self, args: list[str]) -> None:
        """处理落子。"""
        self._ensure_game()
        if len(args) != 2:
            raise ValueError("Usage: move x y (1-based coordinates).")
        row = int(args[1]) - 1
        col = int(args[0]) - 1
        command = MoveCommand(self.game, row, col)
        message = command.execute()
        self.game.add_history(command)
        
        # 记录到录像
        if self.match and self.match.recorder:
            action = PlayerAction.move(row, col)
            self.match.recorder.record_move(
                action, self.game.current_player,
                self.game.board.snapshot()
            )
        
        print(message)
        if self.game.is_over:
            self._handle_game_end()

    def handle_pass(self) -> None:
        """处理 pass。"""
        self._ensure_game()
        command: Command = PassCommand(self.game)
        message = command.execute()
        self.game.add_history(command)
        
        if self.match and self.match.recorder:
            action = PlayerAction.pass_turn()
            self.match.recorder.record_move(
                action, self.game.current_player,
                self.game.board.snapshot()
            )
        
        print(message)
        if self.game.is_over:
            self._handle_game_end()

    def handle_undo(self) -> None:
        """处理悔棋。"""
        self._ensure_game()
        last = self.game.pop_history()
        if not last:
            print("No moves to undo.")
            return
        msg = last.undo()
        print(msg)

    def handle_resign(self) -> None:
        """处理认输。"""
        self._ensure_game()
        command: Command = ResignCommand(self.game)
        message = command.execute()
        self.game.add_history(command)
        
        if self.match and self.match.recorder:
            action = PlayerAction.resign()
            self.match.recorder.record_move(
                action, self.game.current_player,
                self.game.board.snapshot()
            )
        
        print(message)
        self._handle_game_end()

    def handle_save(self, args: list[str]) -> None:
        """保存游戏。"""
        self._ensure_game()
        if len(args) != 1:
            raise ValueError("Usage: save filename.json")
        
        replay_data = None
        if self.match and self.match.recorder:
            replay_data = self.match.recorder.export()
        
        save_game(self.game, args[0], replay_data)
        print(f"Saved to {args[0]}")

    def handle_load(self, args: list[str]) -> None:
        """加载游戏。"""
        if len(args) != 1:
            raise ValueError("Usage: load filename.json")
        
        self.game, replay_data = load_game(args[0])
        self.last_game_type = self.game.name.lower()
        self.last_size = self.game.board.size
        self.ai_mode = False
        
        # 恢复录像记录器
        if replay_data:
            from match.recorder import GameRecorder
            self.match = MatchController()
            self.match.recorder = GameRecorder.from_dict(replay_data)
        
        print(f"Loaded {self.game.name} from {args[0]}")

    # ==================== AI 对战 ====================

    def handle_ai_game(self, args: list[str]) -> None:
        """开始 AI 对战。
        
        用法: ai [game_type] [size] [difficulty] [color]
        - difficulty: easy/medium/hard
        - color: black/white (玩家执黑或执白)
        """
        # 解析参数
        game_type = args[0].lower() if len(args) > 0 else None
        size = int(args[1]) if len(args) > 1 else None
        difficulty_str = args[2].lower() if len(args) > 2 else "easy"
        player_color = args[3].lower() if len(args) > 3 else "black"
        
        if not game_type:
            game_type = input("Choose game (gomoku/go/othello): ").strip().lower()
        if game_type not in {"gomoku", "go", "othello"}:
            raise ValueError("Game type must be 'gomoku', 'go', or 'othello'.")
        
        if size is None:
            if game_type == "othello":
                size = 8
            else:
                size = int(input("Board size (8-19): ").strip())
        
        # 解析难度
        difficulty_map = {
            "easy": AIDifficulty.EASY,
            "medium": AIDifficulty.MEDIUM,
            "hard": AIDifficulty.HARD,
            "1": AIDifficulty.EASY,
            "2": AIDifficulty.MEDIUM,
            "3": AIDifficulty.HARD,
        }
        difficulty = difficulty_map.get(difficulty_str, AIDifficulty.EASY)
        
        # 创建游戏
        self.game = GameFactory.create(game_type, size)
        self.last_game_type = game_type
        self.last_size = size
        self.ai_mode = True
        
        # 创建玩家
        user = self.account_service.get_current_user()
        ai_player = create_ai_player(difficulty, game_type)
        
        if player_color == "black":
            self.black_player = HumanPlayer(user.username if user else "Player", user=user)
            self.white_player = ai_player
            print(f"你执黑，AI({difficulty.name})执白")
        else:
            self.black_player = ai_player
            self.white_player = HumanPlayer(user.username if user else "Player", user=user)
            print(f"AI({difficulty.name})执黑，你执白")
        
        # 创建对局控制器
        self.match = MatchController()
        self.match.start(game_type, size, self.black_player, self.white_player,
                        user.user_id if user else None)
        
        print(f"Started {game_type} vs AI-{difficulty.name} on {size}x{size} board.")
        
        # 如果 AI 先手，自动落子
        if player_color == "white":
            self._ai_turn()

    def _ai_turn(self) -> None:
        """AI 自动落子。"""
        if not self.ai_mode or self.game.is_over:
            return
        
        current_player = self.black_player if self.game.current_player == Stone.BLACK else self.white_player
        
        if current_player.player_type != PlayerType.AI:
            return
        
        print("AI thinking...")
        action = current_player.get_action(self.game)
        
        if action.action_type == ActionType.MOVE:
            command = MoveCommand(self.game, action.row, action.col)
            message = command.execute()
            self.game.add_history(command)
            print(f"AI: {message}")
        elif action.action_type == ActionType.PASS:
            command = PassCommand(self.game)
            message = command.execute()
            self.game.add_history(command)
            print(f"AI: {message}")
        
        # 记录到录像
        if self.match and self.match.recorder:
            self.match.recorder.record_move(
                action, self.game.current_player,
                self.game.board.snapshot()
            )
        
        if self.game.is_over:
            self._handle_game_end()
        else:
            print(BoardRenderer.render(self.game))

    # ==================== 账户管理 ====================

    def handle_login(self) -> None:
        """处理登录。"""
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        result = self.account_service.login(username, password)
        if result.is_success:
            user = result.value
            print(f"Welcome back, {user.username}!")
            print(self.account_service.get_user_stats_display(user))
        else:
            print(f"Login failed: {result.error}")

    def handle_register(self) -> None:
        """处理注册。"""
        username = input("Username (3-20 chars, alphanumeric): ").strip()
        password = input("Password (min 6 chars): ").strip()
        confirm = input("Confirm password: ").strip()
        
        if password != confirm:
            print("Passwords do not match.")
            return
        
        result = self.account_service.register(username, password)
        if result.is_success:
            print(f"Registration successful! Welcome, {username}!")
            # 自动登录
            self.account_service.login(username, password)
        else:
            print(f"Registration failed: {result.error}")

    def handle_logout(self) -> None:
        """处理登出。"""
        if self.account_service.is_logged_in():
            self.account_service.logout()
            print("Logged out.")
        else:
            print("Not logged in.")

    def handle_status(self) -> None:
        """显示当前状态。"""
        user = self.account_service.get_current_user()
        if user:
            print(f"Logged in as: {user.username}")
            print(self.account_service.get_user_stats_display(user))
            
            # 显示各游戏类型战绩
            for game_type, record in user.records.items():
                print(f"  {game_type}: {record.wins}W/{record.losses}L/{record.draws}D")
        else:
            print("Not logged in (Guest mode)")
        
        if self.game:
            print(f"Current game: {self.game.name} ({self.game.board.size}x{self.game.board.size})")

    # ==================== 录像回放 ====================

    def handle_replay(self, args: list[str]) -> None:
        """进入回放模式。
        
        用法: replay filename.json
        """
        if len(args) != 1:
            raise ValueError("Usage: replay filename.json")
        
        replay_data = load_replay(args[0])
        
        self.replay_controller = ReplayController()
        self.replay_controller.load(replay_data)
        self.in_replay_mode = True
        
        meta = self.replay_controller.get_metadata()
        print(f"\n=== 回放模式 ===")
        print(f"游戏: {meta.game_type} ({meta.board_size}x{meta.board_size})")
        print(f"黑方: {meta.black_player}")
        print(f"白方: {meta.white_player}")
        print(f"总步数: {meta.total_moves}")
        print(f"结果: {meta.result}")
        print("\n命令: next/n, prev/p, jump N, auto, stop, exit")
        
        # 显示初始棋盘
        game = self.replay_controller.get_game()
        if game:
            print(BoardRenderer.render(game))

    def _handle_replay_command(self, cmd: str, args: list[str]) -> bool:
        """处理回放模式命令。返回 True 继续回放，False 退出回放。"""
        ctrl = self.replay_controller
        
        if cmd in ("next", "n"):
            move = ctrl.next_move()
            if move:
                print(f"Step {move.move_number}: {move.player} {move.action_type}", end="")
                if move.position:
                    print(f" at ({move.position[0]+1}, {move.position[1]+1})")
                else:
                    print()
                print(BoardRenderer.render(ctrl.get_game()))
            else:
                print("Already at the end.")
        
        elif cmd in ("prev", "p"):
            move = ctrl.prev_move()
            if move:
                print(f"Back to step {move.move_number}")
            else:
                print("Already at the beginning.")
            print(BoardRenderer.render(ctrl.get_game()))
        
        elif cmd == "jump":
            if not args:
                print("Usage: jump N")
            else:
                try:
                    n = int(args[0])
                    ctrl.jump_to(n)
                    print(f"Jumped to step {n}")
                    print(BoardRenderer.render(ctrl.get_game()))
                except ValueError as e:
                    print(f"Error: {e}")
        
        elif cmd == "auto":
            interval = float(args[0]) if args else 1.0
            print(f"Auto playing (interval: {interval}s)... Press Ctrl+C to stop")
            try:
                while True:
                    move = ctrl.next_move()
                    if not move:
                        print("Replay finished.")
                        break
                    print(f"Step {move.move_number}: {move.player} {move.action_type}")
                    print(BoardRenderer.render(ctrl.get_game()))
                    import time
                    time.sleep(interval)
            except KeyboardInterrupt:
                print("\nStopped.")
        
        elif cmd == "stop":
            ctrl.stop()
            print("Stopped.")
        
        elif cmd in ("exit", "quit", "q"):
            self.in_replay_mode = False
            self.replay_controller = None
            print("Exited replay mode.")
            return False
        
        else:
            print("Replay commands: next/n, prev/p, jump N, auto [interval], stop, exit")
        
        return True

    # ==================== 辅助方法 ====================

    def _handle_game_end(self) -> None:
        """处理游戏结束。"""
        print("Game ended.")
        
        # 完成录像
        if self.match and self.match.recorder:
            result_str = "DRAW"
            if self.game.winner == Stone.BLACK:
                result_str = "BLACK_WIN"
            elif self.game.winner == Stone.WHITE:
                result_str = "WHITE_WIN"
            self.match.recorder.finalize(result_str, self.game.board.snapshot())
        
        # 更新战绩
        user = self.account_service.get_current_user()
        if user and self.game:
            # 确定玩家是黑方还是白方
            is_black = (self.black_player and 
                       self.black_player.player_type == PlayerType.HUMAN)
            
            if self.game.winner is None:
                is_win = False
                is_draw = True
            elif is_black:
                is_win = self.game.winner == Stone.BLACK
                is_draw = False
            else:
                is_win = self.game.winner == Stone.WHITE
                is_draw = False
            
            self.account_service.update_record(
                user.user_id,
                self.game.name.lower(),
                is_win,
                is_draw
            )
            print(f"战绩已更新: {self.account_service.get_user_stats_display()}")

    def _parse_game_options(self, args: list[str]) -> tuple[str, int]:
        """解析游戏选项。"""
        if len(args) >= 1:
            game_type = args[0].lower()
        else:
            game_type = input("Choose game (gomoku/go/othello): ").strip().lower()
        
        available = GameFactory.get_available_games()
        if game_type not in available:
            raise ValueError(f"Game type must be one of: {available}")

        if len(args) >= 2:
            size = int(args[1])
        else:
            if game_type == "othello":
                size = 8  # 黑白棋默认 8x8
                print(f"Using default size {size} for Othello")
            else:
                size = int(input("Board size (4-19): ").strip())
        
        if size < 4 or size > 19:
            raise ValueError("Board size must be between 4 and 19.")
        
        return game_type, size

    def _ensure_game(self) -> None:
        """确保游戏已开始。"""
        if not self.game:
            raise GameError("Start or load a game first.")

    def print_help_short(self) -> None:
        """打印简短帮助。"""
        print("Commands: start, move x y, pass, undo, resign, ai, save, load, replay, login, help, exit")

    def print_help_full(self) -> None:
        """打印完整帮助。"""
        print("""
=== 棋类对战平台帮助 ===

【游戏控制】
  start [gomoku|go|othello] [size]  - 开始新游戏
  move x y                          - 落子 (列 x, 行 y, 1-based)
  pass                              - 跳过回合 (围棋/黑白棋)
  undo                              - 悔棋
  resign                            - 认输
  restart                           - 重新开始

【AI 对战】
  ai [game] [size] [difficulty] [color]
    - difficulty: easy/medium/hard (默认 easy)
    - color: black/white (默认 black，即玩家执黑)
    - 例: ai othello 8 medium white

【存档/读档】
  save <file>                       - 保存游戏
  load <file>                       - 加载游戏

【录像回放】
  replay <file>                     - 进入回放模式
  回放命令: next/n, prev/p, jump N, auto, exit

【账户】
  login                             - 登录
  register                          - 注册
  logout                            - 登出
  status                            - 查看状态和战绩

【其他】
  help                              - 显示此帮助
  hide_help / show_help             - 切换简短帮助
  exit / quit                       - 退出程序
""")
