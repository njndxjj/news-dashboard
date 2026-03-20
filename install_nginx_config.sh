#!/bin/bash

# Lumos Nginx 配置安装脚本
# 请以 sudo 权限运行此脚本

if [[ $EUID -eq 0 ]]; then
    # 创建配置目录
    mkdir -p /etc/nginx/conf.d/

    # 写入Nginx配置
    cat > /etc/nginx/conf.d/lumos.conf << 'EOF'
server {
    listen 80;
    server_name 4.78.197.107; # 您的服务器IP

    # 用户端前端页面 (原3000端口)
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 解决跨域问题
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
    }

    # 管理后台页面
    location /admin {
        proxy_pass http://localhost:3000/admin;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 解决跨域问题
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
    }

    # 后端API接口
    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 解决跨域问题
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # 设置访问日志
    access_log /var/log/nginx/lumos.access.log;
    error_log /var/log/nginx/lumos.error.log;
}
EOF

    echo "Nginx配置已写入 /etc/nginx/conf.d/lumos.conf"

    # 测试配置
    if nginx -t; then
        echo "配置测试成功"

        # 重启或重载Nginx
        if systemctl is-active --quiet nginx; then
            systemctl reload nginx
            echo "Nginx配置已重载"
        else
            systemctl start nginx
            systemctl enable nginx
            echo "Nginx服务已启动并设置为开机自启"
        fi

        echo "Lumos Nginx配置安装完成！"
        echo ""
        echo "请确保后端服务正在运行："
        echo "- 端口3000: 前端服务"
        echo "- 端口5000: 后端服务"
        echo ""
        echo "现在可以通过 http://4.78.197.107 访问您的Lumos系统"
    else
        echo "Nginx配置测试失败，请检查配置文件"
        exit 1
    fi
else
    echo "请使用 sudo 权限运行此脚本:"
    echo "sudo $0"
    exit 1
fi