#!/bin/bash

# Lumos 系统服务管理脚本

SERVICE_DIR="/home/ubuntu/lumos"  # 修改为您的实际路径
LOG_FILE="/var/log/lumos_services.log"

case "$1" in
    start)
        echo "Starting Lumos services..."

        # 启动后端服务
        cd $SERVICE_DIR/Lumos/backend
        nohup python3 monitor_app.py > /var/log/monitor_app.log 2>&1 &
        echo $! > /tmp/monitor_app.pid
        echo "Backend service started with PID $(cat /tmp/monitor_app.pid)"

        # 启动前端服务
        cd $SERVICE_DIR/Lumos/frontend-new
        nohup node server.js > /var/log/frontend_server.log 2>&1 &
        echo $! > /tmp/frontend_server.pid
        echo "Frontend service started with PID $(cat /tmp/frontend_server.pid)"

        # 启动定时任务
        cd $SERVICE_DIR/Lumos
        nohup python3 scheduler.py > /var/log/scheduler.log 2>&1 &
        echo $! > /tmp/scheduler.pid
        echo "Scheduler started with PID $(cat /tmp/scheduler.pid)"

        # 等待几秒后启动代理
        sleep 3

        # 启动反向代理
        cd $SERVICE_DIR
        nohup node simple_proxy.js > /var/log/proxy.log 2>&1 &
        echo $! > /tmp/proxy.pid
        echo "Proxy service started with PID $(cat /tmp/proxy.pid)"

        echo "All Lumos services started successfully!"
        ;;

    stop)
        echo "Stopping Lumos services..."

        # 停止所有进程
        if [ -f /tmp/monitor_app.pid ]; then
            kill $(cat /tmp/monitor_app.pid) 2>/dev/null
            rm /tmp/monitor_app.pid
            echo "Backend service stopped"
        fi

        if [ -f /tmp/frontend_server.pid ]; then
            kill $(cat /tmp/frontend_server.pid) 2>/dev/null
            rm /tmp/frontend_server.pid
            echo "Frontend service stopped"
        fi

        if [ -f /tmp/scheduler.pid ]; then
            kill $(cat /tmp/scheduler.pid) 2>/dev/null
            rm /tmp/scheduler.pid
            echo "Scheduler stopped"
        fi

        if [ -f /tmp/proxy.pid ]; then
            kill $(cat /tmp/proxy.pid) 2>/dev/null
            rm /tmp/proxy.pid
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

        if [ -f /tmp/monitor_app.pid ]; then
            if ps -p $(cat /tmp/monitor_app.pid) > /dev/null; then
                echo "Backend service: Running (PID: $(cat /tmp/monitor_app.pid))"
            else
                echo "Backend service: Stopped"
            fi
        else
            echo "Backend service: Not running"
        fi

        if [ -f /tmp/frontend_server.pid ]; then
            if ps -p $(cat /tmp/frontend_server.pid) > /dev/null; then
                echo "Frontend service: Running (PID: $(cat /tmp/frontend_server.pid))"
            else
                echo "Frontend service: Stopped"
            fi
        else
            echo "Frontend service: Not running"
        fi

        if [ -f /tmp/scheduler.pid ]; then
            if ps -p $(cat /tmp/scheduler.pid) > /dev/null; then
                echo "Scheduler: Running (PID: $(cat /tmp/scheduler.pid))"
            else
                echo "Scheduler: Stopped"
            fi
        else
            echo "Scheduler: Not running"
        fi

        if [ -f /tmp/proxy.pid ]; then
            if ps -p $(cat /tmp/proxy.pid) > /dev/null; then
                echo "Proxy service: Running (PID: $(cat /tmp/proxy.pid))"
            else
                echo "Proxy service: Stopped"
            fi
        else
            echo "Proxy service: Not running"
        fi

        # 检查端口占用
        echo ""
        echo "Port status:"
        netstat -tlnp 2>/dev/null | grep -E '(:3000|:5000|:8080)' || ss -tlnp 2>/dev/null | grep -E '(:3000|:5000|:8080)'
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0