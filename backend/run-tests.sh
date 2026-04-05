#!/bin/bash
# 测试运行脚本 - 输出到终端并保存日志

BACKEND_DIR="$(dirname "$0")"
LOGS_DIR="$BACKEND_DIR/logs"
LOG_FILE="$LOGS_DIR/tests.log"

# 创建日志目录
mkdir -p "$LOGS_DIR"

# 运行测试并输出到终端和日志文件
python -m pytest "$@" 2>&1 | tee "$LOG_FILE"
