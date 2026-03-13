# 🚀 服务器部署指南

新闻仪表盘系统 - Docker 一键部署

---

## 📋 系统架构

- **Web 框架**: Flask 3.0 (端口 5000)
- **任务调度**: Cron (每 10 分钟执行) + Supervisor 进程管理
- **数据库**: SQLite (持久化存储)
- **AI 能力**: 通义千问 (DashScope)
- **浏览器自动化**: Playwright + Chromium

---

## 🎯 方式一：Docker Compose 部署（推荐）

### 1. 环境准备

```bash
# 安装 Docker 和 Docker Compose
# Ubuntu/Debian
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
systemctl enable --now docker

# 安装 docker-compose-plugin
apt-get install docker-compose-plugin
```

### 2. 克隆代码

```bash
git clone https://github.com/njndxjj/news-dashboard.git
cd news-dashboard
```

### 3. 配置环境变量

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑环境变量（必填：DASHSCOPE_API_KEY）
vim .env
```

**.env 文件配置**：
```bash
# 通义千问 API Key（必填）
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# 飞书 Webhook（可选，用于告警推送）
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx
```

### 4. 一键启动

```bash
# 构建并启动容器
docker-compose up -d --build
```

### 5. 查看运行状态

```bash
# 查看容器状态
docker-compose ps

# 查看应用日志
docker-compose logs -f news-monitor

# 查看 Supervisor 日志
docker exec news-monitor-app cat /var/log/supervisor/flask-stdout.log
docker exec news-monitor-app cat /var/log/supervisor/cron-stdout.log
```

### 6. 访问服务

打开浏览器访问：`http://你的服务器IP:5000`

---

## 🐳 方式二：纯 Docker 部署

### 1. 构建镜像

```bash
docker build -t news-monitor-with-cron:latest .
```

### 2. 启动容器

```bash
docker run -d \
  --name news-monitor-app \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v /var/run/supervisor:/var/run/supervisor \
  -e DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx \
  -e FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx \
  --restart unless-stopped \
  news-monitor-with-cron:latest
```

---

## 🔧 方式三：本机直接部署（开发调试）

### 1. 安装依赖

```bash
# Python 3.11+
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 Playwright 浏览器
playwright install chromium
```

### 2. 配置环境变量

```bash
export DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
export FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx
```

### 3. 启动服务

```bash
# 启动 Flask 应用
python monitor_app.py
```

### 4. 配置定时任务（可选）

```bash
# 编辑 crontab
crontab -e

# 添加任务（每 10 分钟执行）
*/10 * * * * cd /path/to/news-dashboard && /usr/bin/python run_crawlers.py >> cron.log 2>&1
```

---

## 📊 监控与维护

### 查看实时日志

```bash
# Flask 应用日志
docker exec -it news-monitor-app tail -f /var/log/supervisor/flask-stdout.log

# Cron 任务日志
docker exec -it news-monitor-app tail -f /var/log/supervisor/cron-stdout.log

# Supervisor 日志
docker exec -it news-monitor-app tail -f /var/log/supervisor/supervisord.log
```

### 手动触发数据更新

```bash
# 在容器内执行
docker exec -it news-monitor-app python run_crawlers.py
```

### 重启服务

```bash
# 重启整个容器
docker-compose restart

# 或只重启 Flask 进程
docker exec news-monitor-app supervisorctl restart flask

# 重启 Cron 进程
docker exec news-monitor-app supervisorctl restart cron
```

### 数据备份

```bash
# 备份数据库
docker exec news-monitor-app cp /app/data/data.db ./data_backup_$(date +%Y%m%d).db

# 备份到服务器
scp root@服务器 IP:/path/to/news-dashboard/data/data.db ./backup/
```

---

## 🔍 常见问题排查

### 1. 容器启动失败

```bash
# 查看启动日志
docker-compose logs

# 检查端口占用
docker exec news-monitor-app netstat -tlnp | grep 5000
```

### 2. API Key 配置问题

```bash
# 验证环境变量
docker exec news-monitor-app echo $DASHSCOPE_API_KEY

# 检查 .env 文件是否被正确加载
docker-compose config
```

### 3. 数据库锁定

```bash
# 删除锁定文件
docker exec news-monitor-app rm -f /app/data/data.db-journal
```

### 4. 内存占用过高

编辑 `docker-compose.yml`，调整资源限制：

```yaml
deploy:
  resources:
    limits:
      memory: 4G  # 增加限制
```

---

## 📱 飞书集成（可选）

### 配置飞书 Webhook

1. 在飞书群添加「自定义机器人」
2. 复制 Webhook 地址
3. 添加到 `.env` 文件：

```bash
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx
```

### 测试推送

```bash
docker exec news-monitor-app python feishu_push.py "测试消息"
```

---

## 🔐 安全建议

1. **使用 HTTPS**：通过 Nginx 反向代理配置 SSL
2. **防火墙**：只开放必要的端口（5000）
3. **API Key**：不要提交到 Git，使用 `.env` 文件管理
4. **容器用户**：建议创建非 root 用户运行容器

---

## 📦 资源消耗

- **CPU**: 0.1-0.5 核心（爬虫运行时）
- **内存**: 512MB - 2GB（取决于并发量）
- **磁盘**: 1GB（包括数据库和历史数据）
- **网络**: 每 10 分钟一次爬虫请求

---

## 🎯 下一步

1. 访问 `http://服务器IP:5000` 查看仪表盘
2. 配置域名和 Nginx 反向代理
3. 设置监控告警（Prometheus + Grafana）
4. 定期备份数据库

---

## 🔄 系统更新

### 方式一：一键更新（推荐）

```bash
# 运行更新脚本
./update.sh

# 选择选项 1: 更新到最新版本
```

**更新脚本会自动完成**：
- ✅ 备份当前数据库和版本
- ✅ 拉取最新代码
- ✅ 重新构建 Docker 镜像
- ✅ 平滑重启容器
- ✅ 健康检查验证
- ✅ 清理旧备份（保留最近 7 个）

### 方式二：手动更新

```bash
# 1. 拉取最新代码
cd /path/to/news-dashboard
git pull origin main

# 2. 备份数据（可选但推荐）
docker exec news-monitor-app cp /app/data/data.db ./data/data.db.backup

# 3. 重新构建并启动
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 4. 查看日志确认
docker-compose logs -f
```

### 回滚操作

如果更新后出现问题：

```bash
# 运行更新脚本
./update.sh

# 选择选项 2: 回滚到上一个版本
```

或手动回滚：

```bash
# 停止容器
docker-compose down

# 恢复数据库
cp ./backups/data.db.YYYYMMDD_HHMMSS.bak ./data/data.db

# 重启容器
docker-compose up -d
```

### 查看备份历史

```bash
# 列出所有备份
ls -lh ./backups/

# 或在更新脚本中选择选项 3
./update.sh
# 选择选项 3: 查看备份列表
```

---

**技术支持**: 查看 GitHub Issues 或提交 PR
