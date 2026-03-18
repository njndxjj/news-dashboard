#!/bin/bash

# Lumos 舆情监控系统 - 服务器手动部署脚本
# 使用方法：在服务器上执行 bash server-deploy.sh

set -e

echo "=========================================="
echo "🚀 Lumos 舆情监控系统 - 服务器部署"
echo "=========================================="

# 配置部分
SERVER_IP="121.196.161.147"
BACKEND_PORT=5000
FRONTEND_PORT=3000
PROJECT_DIR="/root/lumos"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查是否在服务器上执行
echo ""
echo "📍 步骤 1/7: 检查环境..."
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "项目目录 $PROJECT_DIR 不存在！"
    echo "请确认你已在服务器上创建了项目目录"
    exit 1
fi
cd "$PROJECT_DIR"
log_info "当前目录：$(pwd)"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js 未安装！"
    echo "请先安装 Node.js: curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash - && sudo yum install -y nodejs"
    exit 1
fi
log_info "Node.js 版本：$(node -v)"

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    log_error "Python3 未安装！"
    exit 1
fi
log_info "Python 版本：$(python3 --version)"

# 检查 npm
if ! command -v npm &> /dev/null; then
    log_error "npm 未安装！"
    exit 1
fi

# 构建前端
echo ""
echo "📦 步骤 2/7: 构建前端..."
if [ -d "frontend-new" ]; then
    cd frontend-new

    # 安装依赖
    log_info "安装前端依赖..."
    npm install

    # 修改 API 配置
    log_info "配置 API 地址为：http://$SERVER_IP:$BACKEND_PORT"
    cat > src/services/api.jsx << 'APIEOF'
import axios from 'axios';

const API_BASE_URL = 'http://121.196.161.147:5000';

export const apiRequest = async (method, endpoint, data) => {
  try {
    const response = await axios({ method, url: `${API_BASE_URL}${endpoint}`, data });
    return response.data;
  } catch (error) {
    console.error(`Error during API request to ${endpoint}:`, error);
    throw error;
  }
};

export const fetchArticles = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/news`);
    return response.data;
  } catch (error) {
    console.error('Error fetching articles:', error);
    return [];
  }
};

export const sendTestNotification = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/notify`, { message: 'Test notification' });
    return response.data;
  } catch (error) {
    console.error('Error sending notification:', error);
  }
};
APIEOF

    # 构建生产版本
    log_info "构建前端生产版本..."
    npm run build

    if [ -d "dist" ]; then
        log_info "前端构建成功！"
        ls -la dist/
    else
        log_error "前端构建失败！dist 目录不存在"
        exit 1
    fi

    cd ..
else
    log_error "frontend-new 目录不存在！"
    exit 1
fi

# 安装后端依赖
echo ""
echo "📦 步骤 3/7: 安装后端依赖..."
if [ -f "backend/requirements.txt" ]; then
    pip3 install -r backend/requirements.txt
    log_info "后端依赖安装完成"
else
    log_warn "backend/requirements.txt 不存在，跳过依赖安装"
fi

# 初始化数据库
echo ""
echo "🗄️  步骤 4/7: 初始化数据库..."
if [ -f "database_init.py" ]; then
    # 备份旧数据库
    if [ -f "database.sqlite3" ]; then
        cp database.sqlite3 database.sqlite3.backup.$(date +%Y%m%d_%H%M%S)
        log_info "已备份旧数据库"
    fi

    python3 database_init.py
    if [ -f "database_updates.sql" ]; then
        sqlite3 database.sqlite3 < database_updates.sql
    fi
    log_info "数据库初始化完成"
else
    log_warn "database_init.py 不存在，跳过数据库初始化"
fi

# 启动后端服务
echo ""
echo "🔧 步骤 5/7: 启动后端服务..."
if [ -f "server.py" ]; then
    # 检查是否已有后端进程在运行
    if pgrep -f "python3 server.py" > /dev/null; then
        log_warn "检测到后端服务已在运行，正在停止..."
        pkill -f "python3 server.py"
        sleep 2
    fi

    # 启动后端
    nohup python3 server.py > backend.log 2>&1 &
    BACKEND_PID=$!
    sleep 3

    if ps -p $BACKEND_PID > /dev/null; then
        log_info "后端服务已启动 (PID: $BACKEND_PID)"
        log_info "后端日志：tail -f backend.log"
    else
        log_error "后端服务启动失败！请查看 backend.log"
        exit 1
    fi
else
    log_error "server.py 不存在！"
    exit 1
fi

# 启动前端服务
echo ""
echo "🌐 步骤 6/7: 启动前端服务..."
if [ -d "frontend-new/dist" ]; then
    cd frontend-new/dist

    # 检查是否已有前端进程在运行
    if pgrep -f "python3 -m http.server 3000" > /dev/null; then
        log_warn "检测到前端服务已在运行，正在停止..."
        pkill -f "python3 -m http.server 3000"
        sleep 2
    fi

    # 使用 Python HTTP 服务器提供静态文件
    nohup python3 -m http.server 3000 > ../../frontend.log 2>&1 &
    FRONTEND_PID=$!
    sleep 2

    cd ../..

    if ps -p $FRONTEND_PID > /dev/null; then
        log_info "前端服务已启动 (PID: $FRONTEND_PID)"
    else
        log_error "前端服务启动失败！请查看 frontend.log"
        exit 1
    fi
else
    log_error "frontend-new/dist 目录不存在！"
    exit 1
fi

# 配置防火墙（如果是 CentOS/RHEL）
echo ""
echo "🔒 步骤 7/7: 检查防火墙配置..."
if command -v firewall-cmd &> /dev/null; then
    if ! firewall-cmd --list-ports | grep -q "3000/tcp"; then
        log_info "开放端口 3000..."
        firewall-cmd --zone=public --add-port=3000/tcp --permanent
        firewall-cmd --reload
    fi
    if ! firewall-cmd --list-ports | grep -q "5000/tcp"; then
        log_info "开放端口 5000..."
        firewall-cmd --zone=public --add-port=5000/tcp --permanent
        firewall-cmd --reload
    fi
    log_info "防火墙配置完成"
else
    log_warn "未检测到 firewall-cmd，请手动确保端口 3000 和 5000 已开放"
fi

# 完成
echo ""
echo "=========================================="
echo "🎉 部署完成！"
echo "=========================================="
echo ""
echo "📱 访问地址："
echo "   前端：http://$SERVER_IP:$FRONTEND_PORT/"
echo "   后端：http://$SERVER_IP:$BACKEND_PORT/"
echo ""
echo "📋 日志文件："
echo "   后端：tail -f backend.log"
echo "   前端：tail -f frontend.log"
echo ""
echo "🛑 停止服务："
echo "   pkill -f 'python3 server.py'"
echo "   pkill -f 'python3 -m http.server 3000'"
echo ""
echo "🔄 重启服务："
echo "   bash $PROJECT_DIR/server-deploy.sh"
echo ""
echo "⏰ 定时任务已配置（10 分钟执行一次爬虫）"
echo ""
echo "=========================================="
