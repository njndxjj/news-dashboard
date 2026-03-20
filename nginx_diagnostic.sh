#!/bin/bash

# Nginx 诊断脚本
# 用于检查 nginx 配置和运行状态

echo "==========================================="
echo "Nginx 诊断脚本"
echo "==========================================="

echo ""
echo "1. 检查 Nginx 是否已安装..."
if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx 未安装"
    echo "请先安装 Nginx:"
    echo "  Ubuntu/Debian: sudo apt install nginx"
    echo "  CentOS/RHEL: sudo yum install nginx"
    exit 1
else
    echo "✅ Nginx 已安装"
    echo "Nginx 版本: $(nginx -v 2>&1)"
fi

echo ""
echo "2. 检查 Nginx 配置语法..."
if nginx -t 2>/dev/null; then
    echo "✅ 配置语法正确"
else
    echo "❌ 配置语法错误"
    echo "显示详细错误信息:"
    nginx -t
fi

echo ""
echo "3. 检查 Nginx 服务状态..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务正在运行"
else
    echo "❌ Nginx 服务未运行"
    echo "尝试启动 Nginx:"
    sudo systemctl start nginx
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 服务启动成功"
    else
        echo "❌ Nginx 服务启动失败"
        echo "查看错误日志:"
        sudo journalctl -u nginx --no-pager -l
    fi
fi

echo ""
echo "4. 检查 Nginx 服务状态详情..."
sudo systemctl status nginx --no-pager

echo ""
echo "5. 检查 80 端口占用情况..."
if netstat -tlnp 2>/dev/null | grep ':80 '; then
    echo "⚠️  80 端口已被占用"
    echo "占用 80 端口的服务:"
    netstat -tlnp 2>/dev/null | grep ':80 '
elif ss -tlnp 2>/dev/null | grep ':80 '; then
    echo "⚠️  80 端口已被占用"
    echo "占用 80 端口的服务:"
    ss -tlnp 2>/dev/null | grep ':80 '
else
    echo "✅ 80 端口可用"
fi

echo ""
echo "6. 检查 Nginx 主配置文件..."
if [ -f /etc/nginx/nginx.conf ]; then
    echo "✅ 主配置文件存在"
    echo "检查主配置文件内容:"
    grep -E "include|conf.d" /etc/nginx/nginx.conf
else
    echo "❌ 主配置文件不存在"
fi

echo ""
echo "7. 检查 Lumos 自定义配置..."
if [ -f /etc/nginx/conf.d/lumos.conf ]; then
    echo "✅ Lumos 配置文件存在"
    echo "Lumos 配置内容:"
    cat /etc/nginx/conf.d/lumos.conf
else
    echo "❌ Lumos 配置文件不存在"
    echo "如果需要，可以安装配置:"
    echo "  sudo cp /path/to/lumos_nginx_config.conf /etc/nginx/conf.d/lumos.conf"
fi

echo ""
echo "8. 检查错误日志..."
if [ -f /var/log/nginx/error.log ]; then
    echo "最近的错误日志:"
    sudo tail -n 20 /var/log/nginx/error.log
else
    echo "没有找到错误日志文件"
fi

echo ""
echo "9. 检查 Lumos 相关服务状态 (端口 3000 和 5000)..."
if netstat -tlnp 2>/dev/null | grep ':3000\|:5000'; then
    echo "✅ Lumos 相关服务正在运行"
    netstat -tlnp 2>/dev/null | grep -E '(:3000|:5000)'
elif ss -tlnp 2>/dev/null | grep ':3000\|:5000'; then
    echo "✅ Lumos 相关服务正在运行"
    ss -tlnp 2>/dev/null | grep -E '(:3000|:5000)'
else
    echo "⚠️  Lumos 相关服务 (3000/5000) 可能未运行"
    echo "请确保前端服务在 3000 端口，后端服务在 5000 端口运行"
fi

echo ""
echo "==========================================="
echo "诊断完成"
echo "==========================================="

echo ""
echo "常用 Nginx 管理命令:"
echo "  检查配置: sudo nginx -t"
echo "  启动: sudo systemctl start nginx"
echo "  重启: sudo systemctl restart nginx"
echo "  停止: sudo systemctl stop nginx"
echo "  重载配置: sudo systemctl reload nginx"
echo "  查看状态: sudo systemctl status nginx"
echo "  查看错误日志: sudo tail -f /var/log/nginx/error.log"