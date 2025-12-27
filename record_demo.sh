#!/bin/bash
# 自动录制演示视频脚本
# 使用方法: ./record_demo.sh

echo "=============================================="
echo "  棋类对战平台 - 视频录制助手"
echo "=============================================="
echo ""
echo "请选择录制方式:"
echo "  1. 使用 asciinema 录制 (推荐，生成 .cast 文件)"
echo "  2. 使用 script 命令录制 (生成文本日志)"
echo "  3. 手动录制 (打开 QuickTime 后运行演示)"
echo ""
read -p "请选择 [1-3]: " choice

cd "$(dirname "$0")"

case $choice in
    1)
        # 检查 asciinema
        if ! command -v asciinema &> /dev/null; then
            echo "asciinema 未安装，正在安装..."
            brew install asciinema
        fi
        echo ""
        echo "开始录制... (录制文件: demo.cast)"
        echo "提示: 录制完成后可以:"
        echo "  - 播放: asciinema play demo.cast"
        echo "  - 上传: asciinema upload demo.cast"
        echo "  - 转GIF: agg demo.cast demo.gif"
        echo ""
        asciinema rec -c "python3 demo_video.py --pexpect" demo.cast
        ;;
    2)
        echo ""
        echo "开始录制... (录制文件: demo.log)"
        script -q demo.log python3 demo_video.py --pexpect
        echo "录制完成! 文件: demo.log"
        ;;
    3)
        echo ""
        echo "请先打开 QuickTime Player 并选择 '文件 > 新建屏幕录制'"
        echo "开始录制屏幕后，按回车键开始演示..."
        read -p ""
        python3 demo_video.py --pexpect
        echo ""
        echo "演示结束! 请在 QuickTime 中停止录制并保存视频"
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac
