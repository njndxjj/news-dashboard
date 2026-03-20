#!/bin/bash

# Lumos 系统服务管理脚本 - 修正版
# 适配实际项目结构

SERVICE_DIR="/Users/bs-00008898/lobsterai/project"  # 修改为当前工作目录
LOG_DIR="$SERVICE_DIR/logs"
LOG_FILE="$LOG_DIR/lumos_services.log"

# 创建日志目录
mkdir -p $LOG_DIR

case "$1" in
    start)
        echo "Starting Lumos services..."

        # 启动后端服务 (monitor_app.py 在 Lumos 目录下)
        cd $SERVICE_DIR/Lumos
        nohup python3 monitor_app.py > $LOG_DIR/monitor_app.log 2>&1 &
        echo $! > /tmp/monitor_app_lumos.pid
        echo "Backend service started with PID $(cat /tmp/monitor_app_lumos.pid)"

        # 启动前端服务
        cd $SERVICE_DIR/Lumos/frontend-new
        nohup node server.js > $LOG_DIR/frontend_server.log 2>&1 &
        echo $! > /tmp/frontend_server_lumos.pid
        echo "Frontend service started with PID $(cat /tmp/frontend_server_lumos.pid)"

        # 启动定时任务
        cd $SERVICE_DIR/Lumos
        nohup python3 scheduler.py > $LOG_DIR/scheduler.log 2>&1 &
        echo $! > /tmp/scheduler_lumos.pid
        echo "Scheduler started with PID $(cat /tmp/scheduler_lumos.pid)"

        # 等待几秒后启动代理
        sleep 3

        # 启动反向代理
        cd $SERVICE_DIR
        nohup node simple_proxy.js > $LOG_DIR/proxy.log 2>&1 &
        echo $! > /tmp/proxy_lumos.pid
        echo "Proxy service started with PID $(cat /tmp/proxy_lumos.pid)"

        echo "All Lumos services started successfully!"
        ;;

    stop)
        echo "Stopping Lumos services..."

        # 停止所有进程
        if [ -f /tmp/monitor_app_lumos.pid ]; then
            kill $(cat /tmp/monitor_app_lumos.pid) 2>/dev/null
            rm /tmp/monitor_app_lumos.pid
            echo "Backend service stopped"
        fi

        if [ -f /tmp/frontend_server_lumos.pid ]; then
            kill $(cat /tmp/frontend_server_lumos.pid) 2>/dev/null
            rm /tmp/frontend_server_lumos.pid
            echo "Frontend service stopped"
        fi

        if [ -f /tmp/scheduler_lumos.pid ]; then
            kill $(cat /tmp/scheduler_lumos.pid) 2>/dev/null
            rm /tmp/scheduler_lumos.pid
            echo "Scheduler stopped"
        fi

        if [ -f /tmp/proxy_lumos.pid ]; then
            kill $(cat /tmp/proxy_lumos.pid) 2>/dev/null
            rm /tmp/proxy_lumos.pid
            echo "Proxy service stopped"
        fi

        echo "All Lumos services stopped."
        ;;

    restart)
        $0 stop
        sleep 2
        $0 start
        ;;

    status)
        echo "Checking Lumos services status..."

        if [ -f /tmp/monitor_app_lumos.pid ]; then
            if ps -p $(cat /tmp/monitor_app_lumos.pid) > /dev/null; then
                echo "Backend service: Running (PID: $(cat /tmp/monitor_app_lumos.pid))"
            else
                echo "Backend service: Stopped"
            fi
        else
            echo "Backend service: Not running"
        fi

        if [ -f /tmp/frontend_server_lumos.pid ]; then
            if ps -p $(cat /tmp/frontend_server_lumos.pid) > /dev/null; then
                echo "Frontend service: Running (PID: $(cat /tmp/frontend_server_lumos.pid))"
            else
                echo "Frontend service: Stopped"
            fi
        else
            echo "Frontend service: Not running"
        fi

        if [ -f /tmp/scheduler_lumos.pid ]; then
            if ps -p $(cat /tmp/scheduler_lumos.pid) > /dev/null; then
                echo "Scheduler: Running (PID: $(cat /tmp/scheduler_lumos.pid))"
            else
                echo "Scheduler: Stopped"
            fi
        else
            echo "Scheduler: Not running"
        fi

        if [ -f /tmp/proxy_lumos.pid ]; then
            if ps -p $(cat /tmp/proxy_lumos.pid) > /dev/null; then
                echo "Proxy service: Running (PID: $(cat /tmp/proxy_lumos.pid))"
            else
                echo "Proxy service: Stopped"
            fi
        else
            echo "Proxy service: Not running"
        fi

        # 检查端口占用
        echo ""
        echo "Port status:"
        lsof -i :3000 :5000 :8080 2>/dev/null || echo "No services currently listening on ports 3000, 5000, or 8080"
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0