#!/bin/bash
# Lumos 系统服务管理脚本
# 用于启动、停止、重启前后端服务

PROJECT_DIR="/Users/bs-00008898/OpenClaw_Data/Lumos"
BACKEND_PORT=5000
FRONTEND_PORT=3002
LOG_DIR="$PROJECT_DIR/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查端口是否被占用
check_port() {
    local port=$1
    lsof -ti :$port > /dev/null 2>&1
    return $?
}

# 杀掉占用端口的进程
kill_port() {
    local port=$1
    local pid=$(lsof -ti :$port)
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}释放端口 $port (PID: $pid)...${NC}"
        kill -9 $pid 2>/dev/null
        sleep 1
    fi
}

# 启动后端服务
start_backend() {
    echo -e "${GREEN}启动后端服务 (端口 $BACKEND_PORT)...${NC}"

    # 检查是否已经在运行
    if check_port $BACKEND_PORT; then
        echo -e "${YELLOW}后端服务已在运行${NC}"
        return 0
    fi

    # 启动 Flask 应用
    cd "$PROJECT_DIR"
    nohup /usr/bin/python3 monitor_app.py > "$LOG_DIR/backend.log" 2>&1 &
    sleep 2

    if check_port $BACKEND_PORT; then
        echo -e "${GREEN}✓ 后端服务启动成功${NC}"
        return 0
    else
        echo -e "${RED}✗ 后端服务启动失败${NC}"
        return 1
    fi
}

# 启动前端服务
start_frontend() {
    echo -e "${GREEN}启动前端服务 (端口 $FRONTEND_PORT)...${NC}"

    # 检查是否已经在运行
    if check_port $FRONTEND_PORT; then
        echo -e "${YELLOW}前端服务已在运行${NC}"
        return 0
    fi

    # 检查 frontend-new 目录是否存在
    if [ ! -d "$PROJECT_DIR/frontend-new" ]; then
        echo -e "${RED}frontend-new 目录不存在${NC}"
        return 1
    fi

    cd "$PROJECT_DIR/frontend-new"

    # 检查是否有 node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}安装依赖...${NC}"
        npm install
    fi

    # 启动 express 服务器
    nohup /opt/homebrew/bin/node server.js > "$LOG_DIR/frontend.log" 2>&1 &
    sleep 2

    if check_port $FRONTEND_PORT; then
        echo -e "${GREEN}✓ 前端服务启动成功${NC}"
        return 0
    else
        echo -e "${RED}✗ 前端服务启动失败${NC}"
        return 1
    fi
}

# 停止服务
stop_services() {
    echo -e "${YELLOW}停止所有服务...${NC}"

    # 停止后端
    if check_port $BACKEND_PORT; then
        kill_port $BACKEND_PORT
        echo -e "${GREEN}✓ 后端服务已停止${NC}"
    fi

    # 停止前端
    if check_port $FRONTEND_PORT; then
        kill_port $FRONTEND_PORT
        echo -e "${GREEN}✓ 前端服务已停止${NC}"
    fi

    # 停止 Python 监控进程
    pkill -f "monitor_app.py" 2>/dev/null
    pkill -f "server.js" 2>/dev/null

    echo -e "${GREEN}所有服务已停止${NC}"
}

# 重启服务
restart_services() {
    stop_services
    sleep 2
    start_backend
    start_frontend
}

# 显示服务状态
show_status() {
    echo -e "${GREEN}========== Lumos 服务状态 ==========${NC}"

    # 后端状态
    if check_port $BACKEND_PORT; then
        echo -e "后端服务 (端口 $BACKEND_PORT): ${GREEN}运行中${NC}"
        echo -e "  访问地址：http://localhost:$BACKEND_PORT"
    else
        echo -e "后端服务 (端口 $BACKEND_PORT): ${RED}未运行${NC}"
    fi

    # 前端状态
    if check_port $FRONTEND_PORT; then
        echo -e "前端服务 (端口 $FRONTEND_PORT): ${GREEN}运行中${NC}"
        echo -e "  访问地址：http://localhost:$FRONTEND_PORT"
    else
        echo -e "前端服务 (端口 $FRONTEND_PORT): ${RED}未运行${NC}"
    fi

    # 定时任务状态
    echo ""
    if crontab -l 2>/dev/null | grep -q "lumos_crontab\|run_crawlers"; then
        echo -e "定时任务：${GREEN}已安装${NC}"
    else
        echo -e "定时任务：${YELLOW}未安装${NC}"
        echo -e "  运行以下命令安装：crontab $PROJECT_DIR/lumos_crontab"
    fi

    echo -e "${GREEN}=====================================${NC}"
}

# 主函数
case "${1:-status}" in
    start)
        start_backend
        start_frontend
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
