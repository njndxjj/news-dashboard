#!/bin/bash

# Lumos 一键部署脚本
# 使用方法：./deploy.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "🚀 Lumos 服务端一键部署脚本"
echo "============================================================"
echo ""

# 步骤 1: 检查环境
log_info "步骤 1: 检查系统环境..."

# 检查 Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    log_success "Python 已安装：$PYTHON_VERSION"
else
    log_error "Python3 未安装，请先安装 Python 3.8+"
    exit 1
fi

# 检查 Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    log_success "Node.js 已安装：$NODE_VERSION"
else
    log_warning "Node.js 未安装，前端将无法启动"
    SKIP_FRONTEND=true
fi

# 检查 npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    log_success "npm 已安装：$NPM_VERSION"
else
    if [ "$SKIP_FRONTEND" = true ]; then
        log_warning "npm 未安装，将跳过前端部署"
    fi
fi

# 检查 Redis（可选）
REDIS_AVAILABLE=false
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        log_success "Redis 已安装并运行中"
        REDIS_AVAILABLE=true
    else
        log_warning "Redis 已安装但未运行，缓存功能将禁用"
    fi
else
    log_warning "Redis 未安装，缓存功能将禁用（可选）"
fi

# 检查 Git
if command -v git &> /dev/null; then
    log_success "Git 已安装"
else
    log_warning "Git 未安装，无法从 Gitee 拉取代码"
fi

echo ""

# 步骤 2: 从 Gitee 同步代码（如果需要）
log_info "步骤 2: 同步代码..."
read -p "是否需要从 Gitee 拉取最新代码？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d ".git" ]; then
        log_info "正在拉取最新代码..."
        git pull origin main
        log_success "代码同步完成"
    else
        read -p "请输入 Gitee 仓库地址：" -r REPO_URL
        if [ -n "$REPO_URL" ]; then
            log_info "正在克隆仓库..."
            git clone "$REPO_URL" .
            log_success "代码克隆完成"
        else
            log_warning "跳过代码同步"
        fi
    fi
else
    log_info "跳过代码同步，使用本地代码"
fi

echo ""

# 步骤 3: 安装后端依赖
log_info "步骤 3: 安装后端 Python 依赖..."
if [ -f "backend/requirements.txt" ]; then
    cd backend
    pip3 install -r requirements.txt
    cd ..
    log_success "后端依赖安装完成"
else
    log_error "未找到 backend/requirements.txt"
    exit 1
fi

echo ""

# 步骤 4: 安装前端依赖（可选）
if [ "$SKIP_FRONTEND" != true ]; then
    log_info "步骤 4: 安装前端依赖..."
    if [ -f "frontend-new/package.json" ]; then
        cd frontend-new
        npm install
        cd ..
        log_success "前端依赖安装完成"
    else
        log_warning "未找到 frontend-new/package.json，跳过前端依赖安装"
    fi
fi

echo ""

# 步骤 5: 数据库初始化
log_info "步骤 5: 初始化数据库..."
read -p "是否需要初始化数据库？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 检查 Neo4j 配置
    read -p "请输入 Neo4j 连接地址 (默认：bolt://localhost:7687): " -r NEO4J_URI
    NEO4J_URI=${NEO4J_URI:-"bolt://localhost:7687"}

    read -p "请输入 Neo4j 用户名 (默认：neo4j): " -r NEO4J_USER
    NEO4J_USER=${NEO4J_USER:-"neo4j"}

    read -sp "请输入 Neo4j 密码：" -r NEO4J_PASSWORD
    echo

    export NEO4J_URI="$NEO4J_URI"
    export NEO4J_USER="$NEO4J_USER"
    export NEO4J_PASSWORD="$NEO4J_PASSWORD"

    cd backend
    python3 init_db.py
    cd ..
    log_success "数据库初始化完成"
else
    log_info "跳过数据库初始化"
fi

echo ""

# 步骤 6: 配置环境变量
log_info "步骤 6: 配置环境变量..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Lumos 环境配置
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=$(openssl rand -hex 32)

# Neo4j 配置
NEO4J_URI=${NEO4J_URI:-"bolt://localhost:7687"}
NEO4J_USER=${NEO4J_USER:-"neo4j"}
NEO4J_PASSWORD=${NEO4J_PASSWORD:-""}

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# API 配置
API_PORT=5000
FRONTEND_PORT=3000
EOF
    log_success "环境变量配置完成 (.env)"
else
    log_info ".env 文件已存在，跳过"
fi

echo ""

# 步骤 7: 启动服务
log_info "步骤 7: 启动服务..."
echo "请选择启动方式:"
echo "1. 全部启动 (后端 + 定时任务 + 前端)"
echo "2. 只启动后端和定时任务"
echo "3. 手动启动 (不自动启动)"
read -p "请选择 (1/2/3): " -r START_MODE
echo

case $START_MODE in
    1)
        log_info "启动后端服务..."
        nohup python3 monitor_app.py > backend.log 2>&1 &
        BACKEND_PID=$!
        log_success "后端已启动 (PID: $BACKEND_PID)"

        log_info "启动定时任务..."
        nohup python3 scheduler.py > scheduler.log 2>&1 &
        SCHEDULER_PID=$!
        log_success "定时任务已启动 (PID: $SCHEDULER_PID)"

        if [ "$SKIP_FRONTEND" != true ]; then
            log_info "启动前端服务..."
            cd frontend-new
            nohup npm start > ../frontend.log 2>&1 &
            FRONTEND_PID=$!
            cd ..
            log_success "前端已启动 (PID: $FRONTEND_PID)"
        fi
        ;;
    2)
        log_info "启动后端服务..."
        nohup python3 monitor_app.py > backend.log 2>&1 &
        BACKEND_PID=$!
        log_success "后端已启动 (PID: $BACKEND_PID)"

        log_info "启动定时任务..."
        nohup python3 scheduler.py > scheduler.log 2>&1 &
        SCHEDULER_PID=$!
        log_success "定时任务已启动 (PID: $SCHEDULER_PID)"
        ;;
    3)
        log_info "跳过自动启动"
        ;;
    *)
        log_error "无效选择"
        ;;
esac

echo ""

# 步骤 8: 健康检查
log_info "步骤 8: 健康检查..."
sleep 3

# 检查后端
if curl -s http://localhost:5000 > /dev/null; then
    log_success "后端服务运行正常 (http://localhost:5000)"
else
    log_warning "后端服务可能未正常启动，请查看 backend.log"
fi

# 检查前端
if [ "$SKIP_FRONTEND" != true ]; then
    if curl -s http://localhost:3000 > /dev/null; then
        log_success "前端服务运行正常 (http://localhost:3000)"
    else
        log_warning "前端服务可能未正常启动，请查看 frontend.log"
    fi
fi

# 检查定时任务
if pgrep -f "scheduler.py" > /dev/null; then
    log_success "定时任务运行正常"
else
    log_warning "定时任务可能未正常启动，请查看 scheduler.log"
fi

echo ""

# 完成
echo "============================================================"
log_success "部署完成！"
echo "============================================================"
echo ""
echo "服务访问地址:"
echo "  - 后端 API: http://localhost:5000"
if [ "$SKIP_FRONTEND" != true ]; then
    echo "  - 前端页面：http://localhost:3000"
fi
echo ""
echo "查看日志:"
echo "  - 后端日志：tail -f backend.log"
echo "  - 调度器日志：tail -f scheduler.log"
if [ "$SKIP_FRONTEND" != true ]; then
    echo "  - 前端日志：tail -f frontend.log"
fi
echo ""
echo "停止服务:"
echo "  - 停止后端：kill $BACKEND_PID"
echo "  - 停止调度器：kill $SCHEDULER_PID"
if [ "$SKIP_FRONTEND" != true ]; then
    echo "  - 停止前端：kill $FRONTEND_PID"
fi
echo ""
echo "============================================================"
