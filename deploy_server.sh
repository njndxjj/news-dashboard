#!/bin/bash

# Lumos 应用服务器部署脚本
# 用于在服务器环境中部署和管理 Lumos 应用程序

echo "========== Lumos 应用服务器部署脚本 =========="

# 检查是否安装了 PM2
if ! command -v pm2 &> /dev/null; then
    echo "错误: 未找到 PM2，请先安装 PM2:"
    echo "npm install -g pm2"
    exit 1
fi

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python3"
    exit 1
fi

# 检查 Node.js 是否安装
if ! command -v node &> /dev/null; then
    echo "错误: 未找到 Node.js，请先安装 Node.js"
    exit 1
fi

# 创建日志目录
mkdir -p logs

echo "开始部署 Lumos 应用..."

# 构建前端应用
echo "正在构建前端应用..."
cd Lumos/frontend-new
npm install --silent
npm run build --silent
cd ../..

# 使用 PM2 启动应用（使用服务器配置）
echo "正在启动应用..."
pm2 start ecosystem.server.config.js

# 确保应用在系统重启后自动启动
pm2 startup
pm2 save

echo ""
echo "========== 部署完成 =========="
echo "Lumos 应用已成功部署到服务器!"
echo ""
echo "访问地址:"
echo "  - 用户端: http://47.238.241.204:3000"
echo "  - 管理后台: http://47.238.241.204:3000/admin"
echo ""
echo "PM2 管理命令:"
echo "  - 查看状态: pm2 status"
echo "  - 查看日志: pm2 logs"
echo "  - 停止应用: pm2 stop all"
echo "  - 重启应用: pm2 restart all"
echo "  - 删除应用: pm2 delete all"
echo ""
echo "日志文件位置:"
echo "  - 前端日志: ./logs/frontend-out.log"
echo "  - 前端错误: ./logs/frontend-error.log"
echo "  - 后端日志: ./logs/backend-out.log"
echo "  - 后端错误: ./logs/backend-error.log"
echo "  - 调度器日志: ./logs/scheduler-out.log"
echo "  - 调度器错误: ./logs/scheduler-error.log"