#!/bin/bash

# Lumos 服务器一键更新脚本
# 使用方法：bash update-server.sh

set -e

echo "🚀 开始更新 Lumos 服务..."

# 进入项目目录
cd /root/lumos/Lumos

# 拉取最新代码
echo "📦 拉取最新代码..."
git pull origin main

# 安装后端依赖（如果有变化）
echo "📦 检查后端依赖..."
cd backend
npm install --production
cd ..

# 构建前端
echo "🔨 构建前端..."
cd frontend-new
npm install
npm run build
cd ..

# 重启服务
echo "🔄 重启服务..."
pm2 restart lumos-backend
pm2 restart lumos-scheduler

# 等待服务启动
sleep 3

# 查看状态
echo "✅ 服务状态："
pm2 status lumos-backend lumos-scheduler

echo ""
echo "🎉 更新完成！"
echo "📋 查看日志：pm2 logs lumos-backend --lines 50"
