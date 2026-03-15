#!/bin/bash
# Lumos 调度器一键重启脚本

cd /Users/bs-00008898/lobsterai/project/Lumos

echo "🔄 正在重启 Lumos 调度器..."

# 1. 停止旧进程
if [ -f scheduler.pid ]; then
    OLD_PID=$(cat scheduler.pid)
    echo "📍 检测到旧进程 PID: $OLD_PID"
    kill $OLD_PID 2>/dev/null
    sleep 2
fi

# 2. 强制清理残留进程
ps aux | grep "scheduler.py" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null

# 3. 清理锁文件
rm -f scheduler.pid scheduler.lock
echo "🧹 已清理锁文件"

# 4. 等待端口释放
sleep 2

# 5. 启动新进程
nohup python3 scheduler.py > scheduler_stdout.log 2>&1 &
NEW_PID=$!

sleep 2

# 6. 验证启动状态
if ps -p $NEW_PID > /dev/null; then
    echo "✅ 调度器已成功重启！"
    echo "📍 新进程 PID: $NEW_PID"
    echo "📋 查看日志：tail -f scheduler.log"
    echo "🛑 停止服务：cat scheduler.pid | xargs kill"
else
    echo "❌ 调度器启动失败，请检查日志："
    tail -n 50 scheduler_stdout.log
fi
