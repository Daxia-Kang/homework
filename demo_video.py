#!/usr/bin/env python3
"""
自动演示脚本 - 用于录制作业展示视频
运行方式: python demo_video.py

功能展示顺序 (约5分钟):
1. 欢迎界面和帮助系统
2. 五子棋对战演示
3. 围棋对战演示 (含提子)
4. 黑白棋对战演示
5. AI 对战演示
6. 账户系统演示 (注册/登录)
7. 存档/读档演示
8. 录像回放演示
9. 结束

使用 asciinema 或 OBS 录制终端即可
"""

import subprocess
import sys
import time
import os

# 演示脚本 - 每一步的输入和等待时间
DEMO_SCRIPT = [
    # ===== 第一部分: 欢迎和帮助 (约30秒) =====
    ("", 2),  # 启动后等待
    ("# 欢迎来到棋类对战平台演示!", 2),
    ("help", 4),  # 显示完整帮助
    ("hide_help", 1),
    
    # ===== 第二部分: 五子棋演示 (约60秒) =====
    ("# === 五子棋演示 ===", 2),
    ("start gomoku 8", 2),
    ("move 4 4", 1.5),  # 黑
    ("move 5 4", 1.5),  # 白
    ("move 4 5", 1.5),  # 黑
    ("move 5 5", 1.5),  # 白
    ("move 4 6", 1.5),  # 黑
    ("move 5 6", 1.5),  # 白
    ("move 4 7", 1.5),  # 黑
    ("move 5 7", 1.5),  # 白
    ("# 悔棋演示", 1),
    ("undo", 2),
    ("undo", 2),
    ("# 继续下棋", 1),
    ("move 6 4", 1.5),  # 白
    ("move 4 7", 1.5),  # 黑
    ("move 6 5", 1.5),  # 白
    ("move 4 8", 2),    # 黑 - 五连胜利!
    ("# 黑方五子连珠获胜!", 3),
    
    # ===== 第三部分: 围棋演示 (约60秒) =====
    ("# === 围棋演示 (含提子) ===", 2),
    ("start go 9", 2),
    ("# 构造提子局面", 1),
    ("move 3 3", 1.5),  # 黑
    ("move 4 3", 1.5),  # 白 - 被包围的子
    ("move 4 2", 1.5),  # 黑
    ("move 1 1", 1.5),  # 白
    ("move 4 4", 1.5),  # 黑
    ("move 2 2", 1.5),  # 白
    ("move 5 3", 2),    # 黑 - 提掉白子!
    ("# 白子被提掉了!", 3),
    ("# 演示 pass 和终局", 1),
    ("pass", 2),
    ("pass", 2),
    ("# 双方连续 pass，游戏结束", 3),
    
    # ===== 第四部分: 黑白棋演示 (约60秒) =====
    ("# === 黑白棋(Othello)演示 ===", 2),
    ("start othello 8", 2),
    ("# 黑白棋初始布局: 中央4子", 2),
    ("move 3 4", 2),  # 黑 - 翻转白子
    ("# 黑子落下，翻转了白子!", 2),
    ("move 3 3", 2),  # 白
    ("move 2 4", 2),  # 黑
    ("move 2 3", 2),  # 白
    ("move 4 2", 2),  # 黑
    ("move 5 3", 2),  # 白
    ("move 6 4", 2),  # 黑
    ("# 黑白棋的特点: 每步都会翻转对方棋子", 3),
    ("resign", 2),
    ("# 认输结束本局", 2),
    
    # ===== 第五部分: AI 对战演示 (约45秒) =====
    ("# === AI 对战演示 ===", 2),
    ("ai othello 8 easy black", 3),
    ("move 3 4", 3),  # 玩家落子
    ("# AI 自动思考并落子", 2),
    ("move 3 3", 3),
    ("move 2 4", 3),
    ("move 4 2", 3),
    ("resign", 2),
    ("# AI 对战支持三种难度: easy/medium/hard", 3),
    
    # ===== 第六部分: 账户系统演示 (约45秒) =====
    ("# === 账户系统演示 ===", 2),
    ("status", 2),
    ("# 当前是游客模式，注册一个账户", 2),
    # 注册需要交互输入，使用特殊标记
    ("REGISTER:demo_user:demo123", 4),
    ("status", 3),
    ("# 登录后可以记录战绩", 2),
    ("start gomoku 8", 2),
    ("move 4 4", 1),
    ("move 5 5", 1),
    ("resign", 2),
    ("status", 3),
    ("# 战绩已自动记录", 2),
    ("logout", 2),
    
    # ===== 第七部分: 存档/读档演示 (约30秒) =====
    ("# === 存档/读档演示 ===", 2),
    ("start othello 8", 2),
    ("move 3 4", 1.5),
    ("move 3 3", 1.5),
    ("move 2 4", 1.5),
    ("save demo_save.json", 2),
    ("# 游戏已保存到 demo_save.json", 2),
    ("start gomoku 8", 2),
    ("# 加载之前保存的黑白棋", 1),
    ("load demo_save.json", 2),
    ("# 成功恢复到之前的局面!", 3),
    
    # ===== 第八部分: 录像回放演示 (约30秒) =====
    ("# === 录像回放演示 ===", 2),
    ("# 先完成一局游戏生成录像", 1),
    ("start gomoku 6", 2),
    ("move 3 3", 1),
    ("move 4 3", 1),
    ("move 3 4", 1),
    ("move 4 4", 1),
    ("move 3 5", 1),
    ("move 4 5", 1),
    ("move 3 6", 1),
    ("move 4 6", 1),
    ("move 3 2", 2),  # 黑方五连
    ("save demo_replay.json", 2),
    ("replay demo_replay.json", 3),
    ("next", 2),
    ("next", 2),
    ("next", 2),
    ("jump 7", 2),
    ("prev", 2),
    ("exit", 2),
    
    # ===== 结束 =====
    ("# === 演示结束 ===", 2),
    ("# 感谢观看! 本平台支持:", 1),
    ("# - 五子棋、围棋、黑白棋", 1),
    ("# - AI 对战 (三种难度)", 1),
    ("# - 账户系统 (注册/登录/战绩)", 1),
    ("# - 存档/读档", 1),
    ("# - 录像回放", 1),
    ("exit", 2),
]


def create_input_file():
    """创建自动输入文件。"""
    lines = []
    for cmd, _ in DEMO_SCRIPT:
        if cmd.startswith("#"):
            # 注释行 - 打印但不作为命令
            continue
        elif cmd.startswith("REGISTER:"):
            # 特殊处理注册
            _, username, password = cmd.split(":")
            lines.append("register")
            lines.append(username)
            lines.append(password)
            lines.append(password)  # 确认密码
        elif cmd.startswith("LOGIN:"):
            _, username, password = cmd.split(":")
            lines.append("login")
            lines.append(username)
            lines.append(password)
        else:
            lines.append(cmd)
    
    with open("demo_input.txt", "w") as f:
        f.write("\n".join(lines))
    
    return "demo_input.txt"


def run_demo_with_pexpect():
    """使用 pexpect 运行交互式演示 (推荐)。"""
    try:
        import pexpect
    except ImportError:
        print("需要安装 pexpect: pip install pexpect")
        return False
    
    print("=" * 60)
    print("  棋类对战平台 - 自动演示")
    print("  预计时长: 约5分钟")
    print("  建议使用 asciinema 或 OBS 录制")
    print("=" * 60)
    print()
    time.sleep(2)
    
    # 启动程序
    child = pexpect.spawn("python3 main.py", encoding="utf-8", timeout=30)
    child.logfile = sys.stdout
    
    try:
        for cmd, delay in DEMO_SCRIPT:
            time.sleep(delay)
            
            if cmd.startswith("#"):
                # 打印注释 (演示说明)
                print(f"\n{'='*50}")
                print(f"  {cmd[2:]}")
                print(f"{'='*50}\n")
                continue
            
            if cmd.startswith("REGISTER:"):
                _, username, password = cmd.split(":")
                child.expect(">")
                child.sendline("register")
                time.sleep(0.5)
                child.expect("Username")
                child.sendline(username)
                time.sleep(0.5)
                child.expect("Password")
                child.sendline(password)
                time.sleep(0.5)
                child.expect("Confirm")
                child.sendline(password)
                continue
            
            if cmd.startswith("LOGIN:"):
                _, username, password = cmd.split(":")
                child.expect(">")
                child.sendline("login")
                time.sleep(0.5)
                child.expect("Username")
                child.sendline(username)
                time.sleep(0.5)
                child.expect("Password")
                child.sendline(password)
                continue
            
            # 等待提示符
            try:
                child.expect(">", timeout=10)
            except pexpect.TIMEOUT:
                pass
            
            # 发送命令
            child.sendline(cmd)
        
        child.expect(pexpect.EOF, timeout=5)
        
    except pexpect.EOF:
        pass
    except pexpect.TIMEOUT:
        print("\n[超时，继续...]")
    finally:
        child.close()
    
    print("\n演示结束!")
    return True


def run_demo_simple():
    """简单模式 - 直接输入文件重定向。"""
    print("=" * 60)
    print("  棋类对战平台 - 自动演示 (简单模式)")
    print("=" * 60)
    
    input_file = create_input_file()
    
    # 使用输入重定向运行
    os.system(f"python3 main.py < {input_file}")
    
    # 清理
    os.remove(input_file)
    print("\n演示结束!")


def run_demo_manual():
    """手动演示模式 - 打印命令序列供手动执行。"""
    print("=" * 60)
    print("  棋类对战平台 - 手动演示指南")
    print("  请按顺序执行以下命令")
    print("=" * 60)
    print()
    
    for i, (cmd, delay) in enumerate(DEMO_SCRIPT, 1):
        if cmd.startswith("#"):
            print(f"\n{'─'*40}")
            print(f"  {cmd[2:]}")
            print(f"{'─'*40}")
        elif cmd.startswith("REGISTER:"):
            _, username, password = cmd.split(":")
            print(f"  {i}. register")
            print(f"     -> 输入用户名: {username}")
            print(f"     -> 输入密码: {password}")
            print(f"     -> 确认密码: {password}")
        elif cmd.startswith("LOGIN:"):
            _, username, password = cmd.split(":")
            print(f"  {i}. login")
            print(f"     -> 输入用户名: {username}")
            print(f"     -> 输入密码: {password}")
        elif cmd:
            print(f"  {i}. {cmd}")
    
    print("\n" + "=" * 60)
    print("  演示结束")
    print("=" * 60)


def run_asciinema_recording():
    """使用 asciinema 自动录制。"""
    try:
        # 检查 asciinema 是否安装
        result = subprocess.run(["which", "asciinema"], capture_output=True)
        if result.returncode != 0:
            print("asciinema 未安装。请运行: brew install asciinema")
            return False
    except:
        print("无法检查 asciinema")
        return False
    
    print("=" * 60)
    print("  使用 asciinema 录制演示视频")
    print("=" * 60)
    print()
    print("录制将保存为 demo_recording.cast")
    print("可以上传到 asciinema.org 或转换为 GIF/MP4")
    print()
    
    # 创建录制脚本
    script_content = '''#!/bin/bash
cd "$(dirname "$0")"
python3 demo_video.py --pexpect
'''
    with open("_record_helper.sh", "w") as f:
        f.write(script_content)
    os.chmod("_record_helper.sh", 0o755)
    
    # 使用 asciinema 录制
    os.system("asciinema rec -c './demo_video.py --pexpect' demo_recording.cast")
    
    # 清理
    os.remove("_record_helper.sh")
    
    print("\n录制完成! 文件: demo_recording.cast")
    print("播放: asciinema play demo_recording.cast")
    print("上传: asciinema upload demo_recording.cast")
    return True


def main():
    """主函数。"""
    print("""
╔══════════════════════════════════════════════════════════╗
║          棋类对战平台 - 自动演示脚本                       ║
╠══════════════════════════════════════════════════════════╣
║  用于录制约5分钟的作业展示视频                             ║
║                                                          ║
║  运行模式:                                                ║
║    1. python demo_video.py --pexpect  (推荐，自动交互)    ║
║    2. python demo_video.py --simple   (简单输入重定向)    ║
║    3. python demo_video.py --manual   (打印命令指南)      ║
║    4. python demo_video.py --record   (asciinema录制)    ║
║                                                          ║
║  录制建议:                                                ║
║    - macOS: 使用 asciinema 或 QuickTime                  ║
║    - 终端放大字体 (Cmd + 加号)                            ║
║    - 使用深色背景主题                                     ║
╚══════════════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "--pexpect":
            run_demo_with_pexpect()
        elif mode == "--simple":
            run_demo_simple()
        elif mode == "--manual":
            run_demo_manual()
        elif mode == "--record":
            run_asciinema_recording()
        else:
            print(f"未知模式: {mode}")
    else:
        # 默认尝试 pexpect，失败则用简单模式
        print("选择运行模式:")
        print("  1. 自动交互演示 (需要 pexpect)")
        print("  2. 简单模式 (输入重定向)")
        print("  3. 手动指南 (打印命令)")
        print("  4. asciinema 录制")
        print()
        
        choice = input("请选择 [1-4]: ").strip()
        
        if choice == "1":
            if not run_demo_with_pexpect():
                print("\n切换到简单模式...")
                run_demo_simple()
        elif choice == "2":
            run_demo_simple()
        elif choice == "3":
            run_demo_manual()
        elif choice == "4":
            run_asciinema_recording()
        else:
            print("无效选择，使用手动指南模式")
            run_demo_manual()


if __name__ == "__main__":
    main()
