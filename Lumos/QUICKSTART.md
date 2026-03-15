# Lumos 快速开始指南

本指南将帮助你在 5 分钟内完成 Lumos 商家洞察系统的部署和首次使用。

---

## 📋 前置要求

### 系统要求
| 系统 | 要求 |
|------|------|
| **操作系统** | macOS / Linux / Windows (WSL) |
| **Python** | 3.9 或更高版本 |
| **Node.js** | 16 或更高版本 (Docker 部署可选) |
| **Docker** | 20.10+ (推荐) |
| **内存** | 2GB+ (Docker) / 4GB+ (本地) |
| **磁盘** | 10GB+ |

### 环境变量准备

创建 `.env` 文件：
```bash
cd Lumos
touch .env
```

编辑 `.env` 文件：
```bash
# ===== 数据库配置 =====
DB_PATH=./data/database.sqlite3

# ===== Qwen 大模型 API Key (必填) =====
# 获取地址：https://dashscope.console.aliyun.com/
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxx

# ===== Neo4j 配置 (可选，用于知识图谱) =====
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# ===== 管理员配置 =====
ADMIN_TOKEN=change-me-please
```

---

## 🚀 部署方式

### 方式一：Docker 部署 (推荐 ⭐)

最简单的方式，适合快速体验，无需安装额外依赖。

```bash
# 1. 克隆项目
git clone https://github.com/njndxjj/news-dashboard.git
cd Lumos

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 DASHSCOPE_API_KEY

# 3. 启动所有服务
docker-compose up -d

# 4. 查看运行状态
docker-compose ps

# 5. 访问应用
# 前端：http://localhost:3000
# 后端 API: http://localhost:5100
```

**常用命令**:
```bash
# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 进入容器调试
docker-compose exec backend bash
```

---

### 方式二：本地开发部署

适合开发者，可以修改代码调试。

#### Step 1: 安装 Python 依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r backend/requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
playwright install-deps chromium
```

#### Step 2: 安装前端依赖

```bash
cd frontend-new
npm install
cd ..
```

#### Step 3: 初始化数据库

```bash
# 创建数据目录
mkdir -p data

# 初始化 SQLite 数据库
python backend/database_init.py
```

#### Step 4: 启动服务

```bash
# 终端 1: 启动后端服务 (端口 5100)
cd backend
flask run --port 5100

# 终端 2: 启动前端开发服务器 (端口 3000)
cd frontend-new
npm run dev
```

访问 http://localhost:3000 开始使用。

---

## ✅ 首次使用检查清单

### 1. 检查服务状态

```bash
# Docker 方式
docker-compose ps

# 应该看到:
# NAME                  STATUS          PORTS
# lumos-backend         Up              0.0.0.0:5100->5100/tcp
# lumos-frontend        Up              0.0.0.0:3000->80/tcp
```

### 2. 检查 API 连通性

```bash
# 测试后端 API
curl http://localhost:5100/api/news/hot

# 应该返回 JSON 数据
```

### 3. 配置 Qwen API Key

如果没有配置 API Key，AI 分析功能将无法使用。

1. 访问 [阿里云百炼控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录阿里云账号
3. 开通 DashScope 服务
4. 创建 API Key
5. 填入 `.env` 文件的 `DASHSCOPE_API_KEY` 字段
6. 重启服务

### 4. 首次登录

访问 http://localhost:3000，你可以：

- **游客模式**: 直接体验基础功能
- **注册账号**: 使用手机号注册，获得个性化推荐

---

## 🔧 常见问题

### Q1: Docker 启动失败

**问题**: `docker-compose up -d` 报错

**解决**:
```bash
# 检查 Docker 是否运行
docker ps

# 重新构建镜像
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Q2: 前端无法连接后端

**问题**: 前端显示"网络错误"

**解决**:
1. 检查后端是否启动：`curl http://localhost:5100/api/health`
2. 检查跨域配置：确保 `.env` 中 `API_URL` 配置正确
3. 清除浏览器缓存后重试

### Q3: AI 分析不工作

**问题**: 新闻没有 AI 分析结果

**解决**:
1. 检查 `DASHSCOPE_API_KEY` 是否正确配置
2. 查看后端日志：`docker-compose logs backend`
3. 确认 API Key 有足够额度

### Q4: 知识图谱无法显示

**问题**: 知识图谱页面空白

**解决**:
1. 确认 Neo4j 是否启动：`docker-compose ps neo4j`
2. 检查 Neo4j 配置是否正确
3. Neo4j 是可选功能，不影响其他功能使用

---

## 📚 下一步

完成部署后，你可以：

1. **浏览热门资讯**: 查看系统聚合的最新商业资讯
2. **设置兴趣标签**: 配置你关注的行业、公司、人物
3. **查看 AI 分析**: 阅读 AI 生成的新闻摘要和洞察
4. **探索知识图谱**: 可视化浏览商业实体关系
5. **配置推送通知**: 设置飞书或邮件推送

---

## 🆘 获取帮助

- **文档**: 查看 [INDEX.md](INDEX.md) 获取完整文档导航
- **Issue**: https://github.com/njndxjj/news-dashboard/issues
- **API 文档**: [API.md](API.md)

---

*Lumos Team © 2026*
