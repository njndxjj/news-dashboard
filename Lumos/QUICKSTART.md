# Lumos 快速开始指南

本指南将帮助你在 5 分钟内完成 Lumos 的部署和首次使用。

---

## 📋 前置要求

### 系统要求
- **操作系统**: macOS / Linux / Windows (WSL)
- **Python**: 3.9 或更高版本
- **Node.js**: 16 或更高版本 (可选，如使用 Docker)
- **Docker**: 20.10+ (可选，Docker 部署需要)

### 环境变量准备
```bash
# 创建 .env 文件
cd Lumos
touch .env
```

编辑 `.env` 文件：
```bash
# 数据库路径
DB_PATH=./database.sqlite3

# Qwen 大模型 API Key (可选，用于 AI 分析)
# 获取地址：https://dashscope.console.aliyun.com/
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxx

# Neo4j 配置 (可选，用于知识图谱)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# 管理员配置
ADMIN_TOKEN=admin-token-change-me-please
```

---

## 🚀 部署方式

### 方式一：Docker 部署 (最简单，推荐⭐)

适合快速体验，无需安装依赖。

```bash
# 1. 克隆项目
git clone https://github.com/njndxjj/lumos.git
cd Lumos

# 2. 启动 Docker 容器
docker-compose up -d

# 3. 初始化数据库
docker-compose exec backend python database_init.py

# 4. 查看运行状态
docker-compose ps

# 5. 访问服务
# 前端：http://localhost:3000
# 后端 API: http://localhost:5100
```

**停止服务**:
```bash
docker-compose down
```

**查看日志**:
```bash
docker-compose logs -f
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
```

#### Step 2: 安装前端依赖

```bash
cd frontend-new
npm install
cd ..
```

#### Step 3: 初始化数据库

```bash
python database_init.py
```

输出示例：
```
数据库表已创建成功！
✅ 初始化完成
```

#### Step 4: 启动后端服务

```bash
cd backend
flask run --port 5100 --debug
```

后端将在 `http://localhost:5100` 启动。

#### Step 5: 启动前端服务 (新终端)

```bash
cd frontend-new
npm run dev
```

前端将在 `http://localhost:5173` 启动。

---

### 方式三：一键部署脚本

```bash
# 赋予执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

脚本会自动完成：
1. ✅ 创建虚拟环境
2. ✅ 安装 Python 依赖
3. ✅ 初始化数据库
4. ✅ 启动后端服务
5. ✅ 启动前端服务

---

## 📱 首次使用

### 1. 访问首页

打开浏览器访问 `http://localhost:3000` (Docker) 或 `http://localhost:5173` (本地开发)。

### 2. 游客体验 (无需注册)

首次访问会自动以游客身份登录，系统会：
- ✅ 分配唯一用户 ID
- ✅ 使用默认兴趣关键词 (AI 相关)
- ✅ 自动加载热门新闻和 AI 分析

### 3. 注册用户 (可选)

如需保存兴趣标签和行为数据：

1. 点击 **登录/注册** 按钮
2. 选择 **手机号注册**
3. 输入手机号，获取验证码
4. 输入验证码，完成注册
5. 设置个人兴趣标签

### 4. 设置兴趣标签

在 **兴趣管理** 面板中选择你关注的领域：
- 📊 科技领域：创业、融资、AI、硬科技...
- 📈 宏观政策：政策、法规、监管...
- 📰 行业趋势：数字化、智能化、市场分析...
- 💼 经营管理：人才、招聘、绩效、战略...
- 📣 市场营销：品牌、电商、获客...
- 💰 财税金融：税务、贷款、上市...
- ⚖️ 法律合规：合同、知识产权、数据合规...
- 🔧 技术升级：自动化、机器人、AI 应用...
- 📦 供应链：采购、物流、库存...

### 5. 查看功能

#### 热门新闻
展示全网实时热点新闻，每 10 分钟自动更新。

#### AI 分析
- **情感分析**: 正面 / 中性 / 负面
- **关键词提取**: 自动提取核心关键词
- **智能摘要**: 一键生成新闻摘要

#### 个性化推荐
根据你的兴趣标签和浏览行为，智能推荐相关内容。

#### 知识图谱 (需配置 Neo4j)
可视化展示新闻中的人物、公司、事件关联关系。

---

## ⚙️ 配置说明

### 启用/禁用数据源

编辑 `config/config.yaml`:

```yaml
platforms:
  # 启用的平台
  - id: "toutiao"
    name: "今日头条"

  # 禁用的平台 (前面加 #)
  # - id: "weibo"
  #   name: "微博"
```

### 修改管理员密码

编辑 `config/config.yaml`:

```yaml
admin:
  users:
    - username: "admin"
      password: "admin123"  # 修改为你的密码
      token: "your-admin-token"
```

---

## 🔧 常见问题

### Q1: 后端启动失败，提示端口被占用
```bash
# 检查端口占用
lsof -i :5100

# 杀死占用端口的进程
kill -9 <PID>

# 或者修改启动端口
flask run --port 5101
```

### Q2: 前端无法连接后端 API
检查 `frontend-new/src/services/api.js` 中的 API 地址配置：
```javascript
const API_BASE_URL = 'http://localhost:5100'; // 确保与后端端口一致
```

### Q3: 数据库初始化失败
```bash
# 删除旧数据库文件
rm database.sqlite3

# 重新初始化
python database_init.py
```

### Q4: 爬虫抓取失败
部分平台可能需要代理或验证码，建议：
1. 检查网络连接
2. 配置代理 (如有)
3. 暂时跳过失败平台，使用 RSS 源

---

## 📊 定时任务配置

Lumos 默认每 10 分钟自动更新新闻数据。

### 查看定时任务状态
```bash
# 查看 crontab 配置
crontab -l

# 查看任务日志
tail -f logs/scheduler.log
```

### 手动触发新闻抓取
```bash
cd backend
python -c "from data_collection import fetch_all_news; fetch_all_news()"
```

---

## 🧪 测试

### 后端测试
```bash
# 安装测试依赖
pip install pytest

# 运行测试
pytest backend/tests/ -v
```

### 前端测试
```bash
cd frontend-new

# 运行单元测试
npm test

# 运行 E2E 测试
npm run test:e2e
```

---

## 📈 监控与维护

### 查看服务状态
```bash
# 后端进程
ps aux | grep flask

# 前端进程
ps aux | grep node

# 数据库文件
ls -lh database.sqlite3
```

### 数据备份
```bash
# 备份数据库
cp database.sqlite3 database.sqlite3.backup.$(date +%Y%m%d)

# 备份配置文件
cp -r config config.backup.$(date +%Y%m%d)
```

### 日志查看
```bash
# 后端日志
tail -f logs/backend.log

# 爬虫日志
tail -f logs/crawlers.log

# 调度器日志
tail -f logs/scheduler.log
```

---

## 🆘 获取帮助

### 系统日志
```bash
# 查看完整的系统日志
docker-compose logs  # Docker 部署
tail -f logs/*.log   # 本地部署
```

### 数据库检查
```bash
# 使用 SQLite 命令行
sqlite3 database.sqlite3

# 查看表结构
.schema

# 查看用户数据
SELECT * FROM Users LIMIT 10;
```

### GitHub Issues
遇到问题可以在 GitHub 提 Issue:
https://github.com/njndxjj/lumos/issues

---

## ✅ 验证清单

部署完成后，请确认以下项目：

- [ ] 后端服务正常运行在 `http://localhost:5100`
- [ ] 前端服务正常运行在 `http://localhost:3000` (或 5173)
- [ ] 数据库文件 `database.sqlite3` 已创建
- [ ] 能够以游客身份登录
- [ ] 能够查看热门新闻列表
- [ ] AI 分析功能正常 (如配置了 API Key)
- [ ] 定时任务每 10 分钟执行一次

---

## 🎉 完成!

恭喜！你已经成功部署了 Lumos 舆情监控系统。

接下来你可以：
1. 📖 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 了解系统架构
2. 🔧 根据需求配置数据源和定时任务
3. 🎨 自定义前端界面和组件
4. 📊 查看用户行为分析和推荐效果

如有任何问题，欢迎随时联系开发团队或提交 Issue！

---

*最后更新：2026-03-15*
