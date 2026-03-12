#!/bin/bash

# 资讯监控系统 - 一键部署脚本
# 适用于 Ubuntu 20.04+ / Debian 10+

set -e

echo "========================================="
echo "  资讯监控系统 - 一键部署脚本"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误：请使用 sudo 运行此脚本${NC}"
    echo "用法：sudo ./deploy.sh"
    exit 1
fi

# 检查 Docker 是否已安装
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}未检测到 Docker，开始安装...${NC}"

    # 安装 Docker
    apt-get update
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io

    echo -e "${GREEN}✓ Docker 安装完成${NC}"
fi

# 检查 Docker Compose 是否已安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}未检测到 Docker Compose，开始安装...${NC}"

    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    echo -e "${GREEN}✓ Docker Compose 安装完成${NC}"
fi

# 启动 Docker 服务
systemctl enable docker
systemctl start docker

echo ""
echo -e "${GREEN}✓ Docker 环境准备完成${NC}"
echo ""

# 配置环境变量
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}请配置环境变量${NC}"
    echo ""

    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ 已创建 .env 文件${NC}"
        echo ""
        echo -e "${RED}重要：请编辑 .env 文件，填入你的 DASHSCOPE_API_KEY${NC}"
        echo "使用命令：vi .env 或 nano .env"
        echo ""
        read -p "按回车键继续..."
    else
        echo -e "${RED}错误：未找到 .env.example 文件${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env 文件已存在${NC}"
fi

# 构建并启动
echo ""
echo -e "${YELLOW}正在构建 Docker 镜像...${NC}"
docker-compose build

echo ""
echo -e "${YELLOW}正在启动服务...${NC}"
docker-compose up -d

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 10

# 检查服务状态
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}  部署成功！${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
    echo "访问地址：http://localhost:5000"
    echo ""
    echo "常用命令："
    echo "  查看日志：docker-compose logs -f"
    echo "  停止服务：docker-compose down"
    echo "  重启服务：docker-compose restart"
    echo ""
else
    echo ""
    echo -e "${RED}=========================================${NC}"
    echo -e "${RED}  部署失败，请检查日志${NC}"
    echo -e "${RED}=========================================${NC}"
    echo ""
    echo "查看日志：docker-compose logs"
    exit 1
fi
