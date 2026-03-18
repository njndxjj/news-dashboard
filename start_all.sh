#!/bin/bash
# 一键启动所有服务
# - 后端服务：5000 端口
# - 前端服务：3000 端口 (Lumos/frontend-new)
# - 反向代理：8080 端口
# - 定时任务：每 10 分钟自动刷新
#
# 环境变量配置（可选）:
#   BACKEND_PORT=5000
#   FRONTEND_PORT=3000
#   PROXY_PORT=8080
#   PID_DIR=/tmp
#   LOG_DIR=/tmp

echo "============================================================"
echo "🚀 启动 NewsNow 全栈服务"
echo "============================================================"

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 加载配置
BACKEND_PORT=${BACKEND_PORT:-5000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
PROXY_PORT=${PROXY_PORT:-8080}
PID_DIR=${PID_DIR:-/tmp}
LOG_DIR=${LOG_DIR:-/tmp}

# 检查端口占用
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "⚠️  端口 $1 已被占用，正在清理..."
        lsof -ti:$1 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# 清理端口
check_port $BACKEND_PORT
check_port $FRONTEND_PORT
check_port $PROXY_PORT

# 启动后端服务
echo ""
echo "📡 [1/3] 启动后端服务 ($BACKEND_PORT 端口)..."
cd "$SCRIPT_DIR/Lumos"
python3 monitor_app.py > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "   ✅ 后端已启动 (PID: $BACKEND_PID)"
echo "   日志：tail -f $LOG_DIR/backend.log"

# 等待后端启动
sleep 3

# 启动前端服务
echo ""
echo "🎨 [2/4] 启动前端服务 ($FRONTEND_PORT 端口)..."
( cd "$SCRIPT_DIR/Lumos/frontend-new" && npm run dev ) > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "   ✅ 前端已启动 (PID: $FRONTEND_PID)"
echo "   日志：tail -f $LOG_DIR/frontend.log"

# 启动反向代理
echo ""
echo "🔄 [3/4] 启动反向代理 ($PROXY_PORT 端口)..."
( cd "$SCRIPT_DIR" && python3 proxy_server.py ) > "$LOG_DIR/proxy.log" 2>&1 &
PROXY_PID=$!
echo "   ✅ 反向代理已启动 (PID: $PROXY_PID)"
echo "   日志：tail -f $LOG_DIR/proxy.log"

# 启动定时刷新任务
echo ""
echo "⏰ [4/4] 启动定时刷新任务 (每 10 分钟自动更新)..."
( cd "$SCRIPT_DIR" && python3 auto_refresh.py ) > "$LOG_DIR/refresh.log" 2>&1 &
REFRESH_PID=$!
echo "   ✅ 定时任务已启动 (PID: $REFRESH_PID)"
echo "   日志：tail -f $LOG_DIR/refresh.log"

# 保存 PID 以便停止
echo $BACKEND_PID > "$PID_DIR/newsnow_backend.pid"
echo $FRONTEND_PID > "$PID_DIR/newsnow_frontend.pid"
echo $PROXY_PID > "$PID_DIR/newsnow_proxy.pid"
echo $REFRESH_PID > "$PID_DIR/newsnow_refresh.pid"

echo ""
echo "============================================================"
echo "✅ 所有服务已启动!"
echo "============================================================"
echo ""
echo "访问方式:"
echo "  🔹 统一入口 (推荐): http://localhost:$PROXY_PORT"
echo "  🔹 前端直连：http://localhost:$FRONTEND_PORT"
echo "  �� 后端直连：http://localhost:$BACKEND_PORT"
echo ""
echo "管理后台:"
echo "  🔹 http://localhost:$PROXY_PORT/admin"
echo "  🔹 http://localhost:$PROXY_PORT/admin/behavior"
echo ""
echo "停止服务:"
echo "  kill \$(cat $PID_DIR/newsnow_backend.pid) \$(cat $PID_DIR/newsnow_frontend.pid) \$(cat $PID_DIR/newsnow_proxy.pid) \$(cat $PID_DIR/newsnow_refresh.pid)"
echo ""
echo "查看日志:"
echo "  后端：tail -f $LOG_DIR/backend.log"
echo "  代理：tail -f $LOG_DIR/proxy.log"
echo "  定时任务：tail -f $LOG_DIR/refresh.log"
echo "============================================================"
