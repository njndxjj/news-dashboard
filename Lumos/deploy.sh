#!/bin/bash

# 项目部署脚本

set -e  # 如果出错，则退出脚本

# 1. 设置虚拟环境
if [ ! -d "venv" ]; then
  echo "⚙️ 创建虚拟环境..."
  python3 -m venv venv
fi

source venv/bin/activate

# 2. 安装Python依赖
echo "📦 安装Python依赖..."
python3 -m pip install -r backend/requirements.txt

# 3. 初始化数据库
if [ -f "database.sqlite3" ]; then
  echo "🗑️ 删除现有数据库..."
  rm database.sqlite3
fi

echo "📂 初始化数据库结构..."
python3 database_init.py

if [ $? -ne 0 ]; then
  echo "❌ 数据库初始化失败，请检查错误日志。"
  exit 1
fi

sqlite3 database.sqlite3 < ./database_updates.sql

echo "✅ 数据库初始化完成！"

# 4. 启动后端服务
cd backend

# 检查 Flask 是否已安装
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Flask 未安装，请安装 Flask 后重试。"
    exit 1
fi

echo "🚀 启动后端服务..."
export FLASK_APP=app.py
python3 -m flask run &
BACKEND_PID=$!
cd ..

# 5. 启动前端
if [ -d "frontend" ]; then
  echo "💻 启动前端开发服务器..."
  cd frontend
  npm install
  npm start &
  FRONTEND_PID=$!
  cd ..
else
  echo "❌ 前端目录不存在，跳过前端启动。"
fi

# 6. 完成
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

echo "🎉 项目已部署完成！前端和后端已启动。按 Ctrl+C 停止服务。"