#!/bin/bash

# Lumos Nginx 配置安装和修复脚本
# 请以 sudo 权限运行此脚本

echo "==========================================="
echo "Lumos Nginx 配置安装和修复脚本"
echo "==========================================="

if [[ $EUID -eq 0 ]]; then
    # 创建配置目录
    mkdir -p /etc/nginx/conf.d/

    # 检测服务器IP
    SERVER_IP=$(curl -s ifconfig.me)
    if [ -z "$SERVER_IP" ]; then
        SERVER_IP="47.238.241.204"  # 使用默认IP
        echo "⚠️  无法检测服务器IP，使用默认IP: $SERVER_IP"
    else
        echo "✅ 检测到服务器IP: $SERVER_IP"
    fi

    # 写入Nginx配置
    cat > /etc/nginx/conf.d/lumos.conf << EOF
server {
    listen 80;
    server_name $SERVER_IP; # 您的服务器IP

    # 用户端前端页面 (原3000端口)
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # 解决跨域问题
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
    }

    # 管理后台页面
    location /admin {
        proxy_pass http://localhost:3000/admin;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # 解决跨域问题
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
    }

    # 后端API接口
    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # 解决跨域问题
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }

    # 设置访问日志
    access_log /var/log/nginx/lumos.access.log;
    error_log /var/log/nginx/lumos.error.log;
}
EOF

    echo "✅ Nginx配置已写入 /etc/nginx/conf.d/lumos.conf"
    echo "配置内容："
    cat /etc/nginx/conf.d/lumos.conf

    # 测试配置
    echo ""
    echo "🔧 测试配置..."
    if nginx -t; then
        echo "✅ 配置测试成功"

        # 检查并安装防火墙规则
        if command -v ufw &> /dev/null; then
            echo "🔍 检测到 UFW 防火墙，开放 HTTP 端口..."
            sudo ufw allow 'Nginx Full' 2>/dev/null || sudo ufw allow 80/tcp
        elif command -v firewall-cmd &> /dev/null; then
            echo "🔍 检测到 firewalld，开放 HTTP 端口..."
            sudo firewall-cmd --permanent --zone=public --add-service=http 2>/dev/null
            sudo firewall-cmd --reload 2>/dev/null
        fi

        # 重启或启动Nginx
        echo "🔄 重启 Nginx 服务..."
        if systemctl is-active --quiet nginx; then
            systemctl reload nginx
            if systemctl is-reload-or-restart --quiet nginx; then
                echo "✅ Nginx配置已重载"
            else
                echo "⚠️ Nginx重载失败，尝试重启..."
                systemctl restart nginx
            fi
        else
            systemctl start nginx
            systemctl enable nginx
            echo "✅ Nginx服务已启动并设置为开机自启"
        fi

        # 检查nginx状态
        echo ""
        echo "📋 检查 Nginx 状态..."
        systemctl status nginx --no-pager

        echo ""
        echo "🎉 Lumos Nginx配置安装和修复完成！"
        echo ""
        echo "请确保后端服务正在运行："
        echo "  - 端口3000: 前端服务"
        echo "  - 端口5000: 后端服务"
        echo ""
        echo "现在可以通过 http://$SERVER_IP 访问您的Lumos系统"
        echo ""
        echo "如果仍有问题，请运行诊断脚本: ./nginx_diagnostic.sh"
    else
        echo "❌ Nginx配置测试失败，请检查配置文件"
        echo "错误详情："
        nginx -t
        exit 1
    fi
else
    echo "❌ 请使用 sudo 权限运行此脚本:"
    echo "   sudo $0"
    exit 1
fi