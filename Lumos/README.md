# Lumos - 智能舆情监控与知识图谱平台

<div align="center">

**一站式热点新闻聚合、AI 分析推荐与知识图谱可视化系统**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://python.org)
[![React](https://img.shields.io/badge/react-18+-blue.svg)](https://react.dev)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)

</div>

---

## 📖 项目介绍

**Lumos** 是一个全功能的智能舆情监控系统，能够实时抓取全网热点新闻，通过 AI 大模型进行智能分析和推荐，并以知识图谱的形式可视化展示信息关联关系。

### 核心特性

- 🔥 **全平台热点聚合** - 支持 60+ 个新闻源，涵盖综合媒体、财经、科技、社交等全领域
- 🤖 **AI 智能分析** - 集成 Qwen 大模型，自动生成新闻摘要、情感分析和关键词提取
- 🎯 **个性化推荐** - 基于用户兴趣标签和行为数据，智能推送相关内容
- 🕸️ **知识图谱** - 使用 Neo4j 构建新闻实体关系网络，可视化展示信息关联
- 📱 **现代前端** - React + Vite 构建，响应式设计，支持多端访问
- 🔐 **用户系统** - 完整的登录/注册/验证码体系，支持游客模式和权限管理
- ⏰ **定时任务** - 每 10 分钟自动更新热点数据，保持信息时效性
- 📊 **用户行为分析** - 内置埋点追踪和用户行为仪表板

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端展示层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ React 18    │ │ Vite        │ │ TailwindCSS │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API 网关层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Flask API   │ │ CORS        │ │ JWT Auth    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      业务逻辑层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 用户模块    │ │ 推荐系统    │ │ 知识图谱    │           │
│  │ User Module │ │ Recommend   │ │ Neo4j       │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 定时调度    │ │ 邮件通知    │ │ 订阅管理    │           │
│  │ Scheduler   │ │ Email       │ │ Subscription│           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据采集层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ RSS Parser  │ │ 爬虫集群    │ │ Browser     │           │
│  │             │ │ Crawlers    │ │ Search      │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ SQLite      │ │ Neo4j       │ │ Redis       │           │
│  │ (主数据库)  │ │ (知识图谱)  │ │ (缓存)      │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
Lumos/
├── backend/                          # 后端服务模块
│   ├── app.py                        # Flask 主应用入口
│   ├── app_knowledge_graph.py        # 知识图谱 API
│   ├── user_module.py                # 用户系统（登录/注册/验证码）
│   ├── recommendation_service.py     # 推荐引擎
│   ├── knowledge_graph.py            # Neo4j 图谱服务
│   ├── task_scheduler.py             # 定时任务调度
│   ├── email_notifications.py        # 邮件通知
│   ├── subscription.py               # 订阅管理
│   ├── realtime_service.py           # 实时推送服务
│   ├── qwen_integration.py           # Qwen 大模型集成
│   ├── snowflake_id.py               # 分布式 ID 生成器
│   └── requirements.txt              # Python 依赖
│
├── frontend-new/                     # 前端 React 应用
│   ├── src/
│   │   ├── App.jsx                   # 主应用组件
│   │   ├── components/               # UI 组件
│   │   │   ├── HotNews.js            # 热点新闻列表
│   │   │   ├── AIAnalysis.js         # AI 分析面板
│   │   │   ├── Recommendation.js     # 个性化推荐
│   │   │   ├── KnowledgeGraph.jsx    # 知识图谱可视化
│   │   │   ├── UserInterests.js      # 兴趣管理
│   │   │   ├── UserBehaviorDashboard.jsx  # 用户行为分析
│   │   │   ├── PushManagement.js     # 推送管理
│   │   │   └── Toast.jsx             # 通知组件
│   │   ├── services/api.js           # API 服务封装
│   │   ├── utils/tracking.js         # 埋点追踪
│   │   └── hooks/useToast.js         # Toast Hook
│   ├── package.json                  # 前端依赖
│   └── vite.config.js                # Vite 配置
│
├── crawlers/                         # 爬虫集群
│   ├── base.py                       # 爬虫基类
│   ├── baidu.py                      # 百度热搜
│   ├── weibo.py                      # 微博
│   ├── zhihu.py                      # 知乎
│   ├── bilibili.py                   # B 站
│   ├── toutiao.py                    # 今日头条
│   ├── kr36.py                       # 36 氪
│   └── xiaohongshu.py                # 小红书
│
├── agents/                           # AI Agent 模块
│   ├── collector/                    # 数据采集 Agent
│   ├── processor/                    # 数据分析 Agent
│   ├── director/                     # 流程编排 Agent
│   └── presenter/                    # 报告生成 Agent
│
├── config/                           # 配置文件
│   ├── config.yaml                   # 平台配置（60+ 数据源）
│   └── rss_mapping.yaml              # RSS 地址映射
│
├── data/                             # 数据目录
│   ├── news_monitor.db               # 新闻监控数据库
│   └── database.sqlite3              # SQLite 主数据库
│
├── browser_search.py                 # 浏览器搜索工具
├── feishu_push.py                   # 飞书推送服务
├── deploy.sh                         # 一键部署脚本
├── docker-compose.yml                # Docker 编排
└── manage_services.sh                # 服务管理脚本
```

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/njndxjj/lumos.git
cd Lumos

# 2. 启动 Docker 容器
docker-compose up -d

# 3. 访问服务
# 前端：http://localhost:3000
# 后端 API: http://localhost:5100
```

### 方式二：本地开发

```bash
# 1. 安装 Python 依赖
pip install -r backend/requirements.txt

# 2. 安装前端依赖
cd frontend-new
npm install

# 3. 初始化数据库
python database_init.py

# 4. 启动后端服务（端口 5100）
cd backend
flask run --port 5100

# 5. 启动前端开发服务器（端口 3000）
cd ../frontend-new
npm run dev
```

### 方式三：一键部署脚本

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📊 支持的数据源

### 综合新闻媒体（11 个）
今日头条、百度热搜、澎湃新闻、凤凰网、参考消息、卫星通讯社、联合早报、MKT 新闻、靠谱新闻、腾讯新闻、虫部落

### 财经投资类（11 个）
华尔街见闻（3 个频道）、财联社（3 个频道）、格隆汇、雪球、金十数据、快讯通、法布财经

### 社交/短视频/娱乐（7 个）
微博、抖音、B 站热搜、贴吧、知乎、虎扑、小红书

### 科技类（11 个）
IT 之家、掘金、GitHub、Hacker News、Solidot、V2EX、牛客网、远景论坛、少数派、ProductHunt、36 氪

### RSS 源配置
详见 [`config/config.yaml`](config/config.yaml)，支持：
- ✅ 动态启用/禁用数据源
- ✅ 自定义平台名称
- ✅ 管理员权限配置

---

## 🔧 核心功能说明

### 1. 用户系统
- **游客模式**：无需注册即可体验基础功能
- **手机号注册**：支持验证码校验
- **登录保护**：防重复点击、验证码防刷
- **兴趣管理**：10 大分类、100+ 预设标签

### 2. AI 分析引擎
- **智能摘要**：自动生成新闻要点
- **情感分析**：正面/负面/中性分类
- **关键词提取**：TF-IDF + Qwen 大模型
- **热点预测**：基于热度趋势分析

### 3. 推荐系统
- **协同过滤**：基于用户行为相似度
- **内容推荐**：基于新闻标签匹配
- **热门榜单**：实时热度排行
- **个性化权重**：用户兴趣优先展示

### 4. 知识图谱
- **实体识别**：人物/机构/地点/事件
- **关系抽取**：投资/竞争/合作等关联
- **可视化展示**：力导向图交互浏览
- **图谱查询**：Cypher 查询语言支持

### 5. 定时任务
- **10 分钟更新**：自动抓取最新热点
- **失败重试**：异常自动恢复
- **任务监控**：执行状态实时查看
- **日志记录**：完整追踪可审计

---

## 🔌 API 接口文档

### 用户相关
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/users/register` | POST | 用户注册/游客登录 |
| `/api/users/send-code` | POST | 发送验证码 |
| `/api/users/verify-code` | POST | 验证验证码 |
| `/api/users/subscriptions` | GET | 获取用户订阅 |
| `/api/users/interests` | POST | 更新兴趣标签 |

### 新闻相关
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/news/hot` | GET | 获取热门新闻 |
| `/api/news/recommend` | GET | 获取推荐新闻 |
| `/api/news/analysis` | GET | 获取 AI 分析结果 |
| `/api/news/search` | GET | 搜索新闻 |

### 知识图谱
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/graph/nodes` | GET | 获取图谱节点 |
| `/api/graph/relations` | GET | 获取关系网络 |
| `/api/graph/query` | POST | Cypher 查询 |

### 管理员功能
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/admin/users` | GET | 用户管理（需 Token） |
| `/api/admin/interests` | GET | 兴趣图谱管理 |
| `/api/admin/scheduler` | POST | 任务调度控制 |

---

## ⚙️ 配置说明

### 环境变量
创建 `.env` 文件并配置：
```bash
# 数据库
DB_PATH=./database.sqlite3

# Neo4j 知识图谱
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Qwen 大模型
DASHSCOPE_API_KEY=your_api_key

# 管理员 Token
ADMIN_TOKEN=admin-token-change-me-please
```

### 配置文件
- **config.yaml**: 数据源启用配置
- **rss_mapping.yaml**: RSS 地址映射表

---

## 📈 监控与运维

### 服务状态检查
```bash
# 查看服务运行状态
./manage_services.sh status

# 重启后端服务
./manage_services.sh restart backend

# 查看定时任务日志
tail -f logs/scheduler.log
```

### 数据库备份
```bash
# 备份 SQLite 数据库
cp database.sqlite3 database.sqlite3.backup.$(date +%Y%m%d)

# 导出 Neo4j 数据
neo4j-admin dump --to=/backup/neo4j.dump
```

---

## 🧪 测试

```bash
# 后端单元测试
pytest backend/tests/

# 前端组件测试
cd frontend-new
npm test

# E2E 测试
python tests/e2e_test.py
```

---

## 📝 开发指南

### 添加新的数据源
1. 在 `config/config.yaml` 中添加配置
2. 在 `crawlers/` 目录下创建爬虫文件
3. 继承 `BaseCrawler` 类实现 `fetch()` 方法
4. 注册到数据采集模块

### 扩展 AI 分析能力
1. 修改 `backend/qwen_integration.py`
2. 调整 Prompt 模板
3. 更新分析结果处理逻辑

### 自定义前端组件
1. 在 `frontend-new/src/components/` 创建组件
2. 导入并在 `App.jsx` 中使用
3. 运行 `npm run dev` 热更新预览

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 开源协议

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 👥 核心团队

- 开发团队：Lumos Team
- GitHub: [@njndxjj](https://github.com/njndxjj/lumos)

---

## 🙏 致谢

本项目使用了以下开源项目：
- [React](https://react.dev/) - 前端框架
- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [Neo4j](https://neo4j.com/) - 图数据库
- [Qwen](https://github.com/QwenLM/Qwen) - 大语言模型

---

<div align="center">

**Made with ❤️ by Lumos Team**

[⬆ 返回顶部](#lumos---智能舆情监控与知识图谱平台)

</div>
