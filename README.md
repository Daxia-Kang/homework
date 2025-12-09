# 棋类对战平台设计文档（草稿）

## 设计目标与需求概述
- 支持五子棋、围棋的双人对战（命令行）。
- 统一交互指令：start、move、pass、undo、resign、save、load、restart、help 等。
- 保存/加载局面，允许悔棋，提供异常提示。
- 体现面向对象设计原则与多种设计模式，易于扩展到新棋种或新 UI。

## 架构与模块
- `core/board.py`：棋盘与坐标、棋子表示。
- `core/game.py`：抽象游戏模板、命令基类与工厂。
- `core/gomoku.py`：五子棋规则。
- `core/go.py`：围棋规则（提子、自杀点判定、简化数目）。
- `storage/save_load.py`：JSON 存档读写。
- `ui/console.py`：命令行交互与渲染。
- `tests/demo.py`：演示/手工测试脚本。
- `main.py`：程序入口。

## 设计模式
- 策略/模板方法：`Game` 抽象类定义通用行棋流程，`GomokuGame` 与 `GoGame` 实现各自规则。
- 简单工厂：`GameFactory.create` 根据用户选择实例化具体游戏。
- 命令模式：`MoveCommand`、`PassCommand`、`ResignCommand` 封装一步操作，支持统一 `execute/undo`，便于悔棋。
- 单一职责的渲染器：`BoardRenderer` 专责输出棋盘。

## 面向对象原则体现
- SRP：棋盘/规则/存档/UI 分层；每个类聚焦单一职责。
- OCP：新增棋种时只需继承 `Game` 并在工厂注册；UI 基于抽象接口不修改。
- LSP：`GomokuGame` 与 `GoGame` 可替换 `Game` 使用，命令对具体类型透明。
- DIP：UI 依赖 `Game` 抽象和 `Command` 接口而非具体实现；存档通过工厂解耦。

## 关键类与方法
- `Board`：`set/get/neighbors/is_on_board/snapshot/restore`。
- `Game`：`execute_move/execute_pass/execute_resign/undo_move/undo_pass/undo_resign`，`record_state/restore_state`，维护当前玩家、胜负、悔棋栈。
- `GomokuGame._check_five_in_row`：连五判定。
- `GoGame._collect_group/_calculate_area_score`：提子与简化数目（地+子）。
- `Command` 族：`execute/undo` 统一接口，悔棋通过恢复 `MoveDelta`/`PassRecord` 等状态。
- `save_game/load_game`：序列化棋盘、玩家、棋种、行棋方、结束状态等。
- `ConsoleUI`：解析指令，创建命令对象，调用核心逻辑并渲染。

## UML（PlantUML 文本）
```
@startuml
abstract class Game {
  board: Board
  current_player: Stone
  winner: Stone?
  pass_count: int
  execute_move()
  execute_pass()
  execute_resign()
  undo_move()
}
class GomokuGame
class GoGame
Game <|-- GomokuGame
Game <|-- GoGame

class Command {
  execute()
  undo()
}
Command <|-- MoveCommand
Command <|-- PassCommand
Command <|-- ResignCommand

class Board {
  grid
  neighbors()
}

class GameFactory {
  +create(type, size): Game
}

ConsoleUI ..> GameFactory
ConsoleUI ..> Command
GameFactory ..> Game
Game ..> Board
MoveCommand ..> Game
PassCommand ..> Game
ResignCommand ..> Game
@enduml
```

## 简化围棋胜负判定说明
- 使用“面积”计分：胜负由「己方棋子数 + 完全被己方包围的空点数」比较。
- 双方连续 `pass` 或棋盘填满时结算。
- 自杀点禁止（除非提掉对方棋块后产生气）。

## 悔棋策略
- 基于命令模式与差异记录（`MoveDelta`/`PassRecord`）恢复棋盘、当前行棋方、pass 计数、胜负状态。
- 悔棋次数默认不限；历史栈为空时给出提示。

## 测试用例（演示）
- 五子棋连五：
  - 输入：`start gomoku 8`，连续在 (1,1)(1,2)(1,3)(1,4)(1,5) 交替落子。
  - 期望：黑方胜，游戏结束。
- 围棋提子：
  - 输入：`start go 9`，构造打吃形后落子提掉对方棋块。
  - 期望：被包围棋块被移除，棋盘更新。
- 连续 pass 终局：
  - 输入：`pass` 两次。
  - 期望：进入结算，根据面积计分输出胜者或平局。
- 非法输入：
  - 越界/已有棋子/自杀点/未知指令，打印错误信息，不改变局面。

## 运行与操作说明
1. 终端执行 `python main.py`。
2. 主要指令：
   - `start [gomoku|go] [size]`
   - `move x y`（列 x, 行 y，1-based）
   - `pass`（仅围棋）
   - `undo`、`resign`、`restart`、`save file.json`、`load file.json`
   - `hide_help` / `show_help` 切换简短帮助；`exit` 退出。
3. 存档示例：`save game1.json`；载入：`load game1.json`。

## 扩展思路
- 新棋种：继承 `Game`，实现 `_apply_move/_post_move/undo_move`，在工厂注册。
- AI 对手：在 UI 层注入“玩家策略”对象，仍复用核心规则。
- 图形界面：替换/并行新增渲染器，依旧调用核心层。

