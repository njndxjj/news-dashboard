# CentOS 7.9 手动部署指南

## 快速部署（一键执行）

在你的阿里云 ECS 终端中执行以下命令：

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
systemctl enable docker
systemctl start docker

# 2. 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 3. 创建应用目录
mkdir -p /opt/lumos/data
cd /opt/lumos

# 4. 下载项目代码
git clone https://github.com/njndxjj/lumos.git . 2>/dev/null || {
    echo "代码已存在，跳过克隆..."
    git pull origin main
}

# 5. 创建 Docker Compose 配置
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  lumos:
    build: .
    container_name: lumos
    restart: always
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - /ms-playwright:/ms-playwright
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - FEISHU_WEBHOOK=${FEISHU_WEBHOOK}
      - BROWSER_SEARCH_ENABLED=true
    network_mode: "host"
    cap_add:
      - SYS_ADMIN
    devices:
      - /dev/kmsg
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/news"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF

# 6. 创建环境变量文件
cat > .env << 'EOF'
# 通义千问 API Key
DASHSCOPE_API_KEY=

# 飞书 Webhook（可选）
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/your_webhook_here
EOF

# 7. 编辑 .env 文件配置你的 API Key（重要！）
echo ""
echo "⚠️  请执行以下命令编辑 .env 文件，配置你的 API Key："
echo "   vi .env"
echo ""

# 8. 构建并启动
echo "构建 Docker 镜像（可能需要几分钟）..."
docker-compose build

echo "启动容器..."
docker-compose up -d

# 9. 查看状态
echo ""
echo "========================================"
echo "  部署完成！"
echo "========================================"
echo ""
echo "📊 查看运行状态：docker-compose ps"
echo "📝 查看日志：docker-compose logs -f"
echo "🌐 访问地址：http://ip:5000"
echo ""
echo "🔧 常用命令："
echo "  - 重启服务：docker-compose restart"
echo "  - 停止服务：docker-compose stop"
echo "  - 查看日志：docker-compose logs -f"
```

## 定时任务配置

部署完成后，编辑 crontab：

```bash
crontab -e
```

添加以下内容（每 10 分钟执行一次）：

```
*/10 * * * * curl http://localhost:5000/api/crawl
```

## 验证部署

```bash
# 检查容器状态
docker-compose ps

# 检查 API 是否正常
curl http://localhost:5000/api/news

# 查看实时日志
docker-compose logs -f
```

## 防火墙配置

如果无法访问，检查防火墙：

```bash
# 开放 5000 端口
firewall-cmd --permanent --add-port=5000/tcp
firewall-cmd --reload

# 或者临时关闭防火墙
systemctl stop firewalld
```
