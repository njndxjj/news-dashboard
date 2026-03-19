#!/bin/bash

# Lumos 后端启动脚本
echo "🚀 正在启动 Lumos 后端服务..."
echo ""

# 检查 Redis 是否运行
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis 服务运行中"
    else
        echo "⚠️  Redis 未运行，尝试启动..."
        brew services start redis 2>/dev/null || echo "   未安装 Redis，缓存功能将禁用"
    fi
else
    echo "⚠️  Redis 未安装，缓存功能将禁用"
    echo "   安装命令：brew install redis"
fi

echo ""
echo "📍 工作目录：$(pwd)"
echo "🔗 API 地址：http://localhost:5001"
echo ""
echo "正在启动 Flask 服务..."
echo "-----------------------------------"

# 启动后端
python3 monitor_app.py
