# 资讯监控系统

一个基于 Flask 的智能化资讯监控系统，支持多平台新闻采集、AI 智能分析、关键词云图、兴趣匹配推荐等功能。

## ✨ 功能特性

- 📰 **多平台采集**：支持 39+ 个科技媒体平台自动抓取
- 🔥 **热度分析**：智能计算新闻热度分数，识别热门话题
- ☁️ **关键词云图**：可视化展示核心关键词分布
- 🎯 **兴趣匹配**：根据用户兴趣智能推荐相关新闻
- 🤖 **AI 推荐**：基于通义千问模型的智能新闻摘要和推荐
- 📱 **社交分析**：追踪社交平台传播趋势
- 🚀 **飞书推送**：支持 webhook 推送高热新闻到飞书群

---

## 🚀 快速部署

### 方案一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone <your-repo-url> news-monitor
cd news-monitor

# 2. 配置环境变量
cp .env.example .env
vi .env  # 填入你的 DASHSCOPE_API_KEY

# 3. 一键启动
docker-compose up -d --build

# 4. 访问应用
# 浏览器打开：http://localhost:5000
```

**一键部署脚本（Ubuntu/Debian）：**
```bash
sudo ./deploy.sh
```

### 方案二：本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 安装 Playwright 浏览器
playwright install chromium
playwright install-deps chromium

# 3. 配置环境变量
cp .env.example .env
vi .env

# 4. 启动服务
python monitor_app.py
```

### 方案三：生产环境部署

详细部署文档请查看：[DEPLOY.md](DEPLOY.md)

包括：
- Docker 生产环境配置
- 云服务器部署（Ubuntu/CentOS）
- Nginx 反向代理配置
- HTTPS 证书配置
- systemd 服务管理
- PaaS 平台部署

---

## 📁 项目结构

```
news-monitor/
├── monitor_app.py          # 主应用（Flask 后端）
├── database.py             # 数据库管理
├── feishu_push.py          # 飞书推送模块
├── templates/
│   └── index.html          # 前端页面
├── static/                 # 静态资源
├── data/                   # 数据存储（SQLite + 缓存）
├── config/
│   ├── config.yaml         # 平台配置
│   └── rss_mapping.yaml    # RSS 源映射
├── crawlers/               # 爬虫模块
├── Dockerfile              # Docker 镜像构建
├── docker-compose.yml      # Docker Compose 配置
├── .env.example            # 环境变量示例
├── deploy.sh               # 一键部署脚本
└── DEPLOY.md               # 详细部署文档
```

---

## ⚙️ 配置说明

### 环境变量

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `DASHSCOPE_API_KEY` | ✅ | 通义千问 API Key |
| `FEISHU_WEBHOOK` | ❌ | 飞书推送 Webhook 地址 |
| `PORT` | ❌ | 服务端口（默认 5000） |
| `FLASK_ENV` | ❌ | 运行环境（production/development） |

### 获取 API Key

1. 访问 [阿里云百炼控制台](https://dashscope.console.aliyun.com/)
2. 开通通义千问服务
3. 创建 API Key
4. 填入 `.env` 文件

---

## 📖 使用说明

### 首页功能

- **热点概览**：展示今日热点新闻 TOP10
- **关键词云图**：可视化核心关键词（点击可搜索）
- **兴趣匹配分析**：显示新闻与用户兴趣的匹配度
- **AI 推荐**：智能生成新闻摘要和推荐
- **社交分析**：追踪社交平台传播趋势

### 搜索功能

- 支持关键词搜索
- 支持情感过滤（全部/正面/中性/负面）
- 支持自动翻译英文标题

### 自定义规则

- 访问 `/rules` 页面管理推送规则
- 设置热度阈值
- 配置关键词过滤

---

## 🔧 技术栈

- **后端**：Python 3.11 + Flask 3.0
- **数据库**：SQLite
- **AI 模型**：通义千问（DashScope）
- **爬虫**：Playwright + feedparser
- **前端**：原生 HTML + CSS + JavaScript
- **部署**：Docker + Docker Compose

---

## 🛠️ 运维命令

### Docker 方式
```bash
# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新部署
git pull
docker-compose up -d --build

# 进入容器调试
docker exec -it news-monitor-app bash
```

### 本地运行方式
```bash
# 查看日志
tail -f app.log

# 重启服务
pkill -f monitor_app.py
nohup python monitor_app.py > app.log 2>&1 &
```

---

## 📊 性能要求

| 部署方式 | 内存 | CPU | 磁盘 |
|----------|------|-----|------|
| Docker | 2GB+ | 2 核 + | 10GB+ |
| 本地运行 | 4GB+ | 2 核 + | 10GB+ |

---

## 🔐 安全建议

1. **不要将 `.env` 文件提交到 Git**
2. 使用 HTTPS（生产环境必须）
3. 配置防火墙规则
4. 定期更新 API Key
5. 限制访问 IP（可选）

---

## 📝 更新日志

### v2.0 - 2024
- ✨ 新增关键词云图可视化
- ✨ 新增兴趣匹配分析
- ✨ 新增 AI 智能推荐
- 🎨 优化界面布局和样式
- 🐛 修复已知问题

### v1.0 - 2024
- 🎉 首次发布
- 支持 39+ 平台采集
- 基础热度分析功能

---

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证

---

## 🙏 致谢

- 感谢使用本项目的每一位用户
- 感谢阿里云提供的 AI 能力支持

---

## 📮 联系方式

如有问题或建议，请提 Issue 或联系开发者。
