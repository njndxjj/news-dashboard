# Lumos - 商家洞察系统

<div align="center">

**基于 AI 个性化推荐的中小企业商业机会发现引擎**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://python.org)
[![React](https://img.shields.io/badge/react-18+-blue.svg)](https://react.dev)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)

</div>

---

## 💡 项目愿景

**Lumos**（拉丁语意为"光"）致力于成为中小企业主的商业洞察之光，帮助他们在复杂多变的商业环境中捕捉机会、洞察趋势、做出明智决策。

> 每个中小企业老板都值得拥有一个专属的商业情报官 —— Lumos 就是这个角色。

---

## 🎯 产品定位

### 为谁而做？

- **中小企业主/创始人**：需要敏锐捕捉行业动态和商业机会
- **创业者**：寻找市场空白和投资机会
- **业务负责人**：关注竞争对手和市场趋势
- **投资人**：快速了解行业动态和潜在标的

### 解决什么问题？

| 痛点 | Lumos 方案 |
|------|-----------|
| 信息过载，难以筛选 | AI 智能过滤，只推送高价值信息 |
| 错过重要商机 | 7×24 小时监控，实时预警 |
| 不了解竞争对手 | 竞品动态追踪，竞争情报分析 |
| 决策缺乏依据 | 数据驱动的洞察报告 |
| 时间有限 | 个性化推荐，只看最相关的 |

---

## ✨ 核心特性

### 🔍 商业机会发现
- **热点捕捉**：实时监控 60+ 数据源，识别行业热点
- **趋势预测**：基于 AI 分析预测行业发展趋势
- **机会推荐**：根据你的业务标签智能推荐商机

### 🎯 个性化推荐引擎
- **兴趣图谱**：记录你的关注点，越用越懂你
- **智能排序**：基于点击、收藏、分享行为优化推荐
- **关键词订阅**：关注特定公司、人物、技术方向

### 🧠 AI 智能分析
- **Qwen 大模型集成**：自动生成新闻摘要和洞察
- **情感分析**：判断舆情走向（正面/负面/中性）
- **实体识别**：自动识别公司、人物、产品、投资事件

### 📊 知识图谱可视化
- **Neo4j 图数据库**：构建商业实体关系网络
- **关系挖掘**：发现公司投资、竞争、合作关系
- **可视化探索**：力导向图交互浏览商业关系

### 🔔 实时通知
- **飞书集成**：高热资讯自动推送到飞书群
- **邮件订阅**：每日/周精选报告
- **阈值告警**：重要关键词动态实时提醒

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ React Web   │ │ Mobile Web  │ │ Admin Dash  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API 服务层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Flask REST  │ │ JWT Auth    │ │ Rate Limit  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      业务服务层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 推荐引擎    │ │ 知识图谱    │ │ 用户系统    │           │
│  │ Recommend   │ │ Neo4j Graph │ │ User Mgmt   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ AI 分析     │ │ 定时调度    │ │ 通知服务    │           │
│  │ AI Analysis │ │ Scheduler   │ │ Notification│           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据采集层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ RSS Parser  │ │ Crawler     │ │ Browser     │           │
│  │             │ │ Cluster     │ │ Automation  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ SQLite      │ │ Neo4j       │ │ Redis       │           │
│  │ (业务数据)  │ │ (知识图谱)  │ │ (缓存)      │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
Lumos/
├── backend/                          # Flask 后端服务
│   ├── monitor_app.py                # 主应用入口
│   ├── recommendation_service.py     # 推荐引擎
│   ├── knowledge_graph.py            # Neo4j 图谱服务
│   ├── qwen_integration.py           # Qwen 大模型集成
│   └── ...
│
├── frontend-new/                     # React 前端应用
│   ├── src/
│   │   ├── App.jsx                   # 根组件
│   │   ├── components/               # UI 组件
│   │   │   ├── HotNews.js            # 热门资讯
│   │   │   ├── AIAnalysis.js         # AI 分析面板
│   │   │   ├── Recommendation.js     # 个性化推荐
│   │   │   ├── KnowledgeGraph.jsx    # 知识图谱
│   │   │   └── UserInterests.js      # 兴趣管理
│   │   └── services/api.js           # API 服务
│   └── ...
│
├── crawlers/                         # 爬虫集群
│   ├── base.py                       # 爬虫基类
│   ├── baidu.py                      # 百度热搜
│   ├── weibo.py                      # 微博
│   ├── kr36.py                       # 36 氪
│   └── ...
│
├── config/                           # 配置文件
│   ├── config.yaml                   # 60+ 数据源配置
│   └── rss_mapping.yaml              # RSS 地址映射
│
├── data/                             # 数据目录
│   ├── database.sqlite3              # SQLite 主数据库
│   └── neo4j/                        # Neo4j 数据
│
└── docker-compose.yml                # Docker 编排
```

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/njndxjj/news-dashboard.git
cd Lumos

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 DASHSCOPE_API_KEY

# 3. 启动所有服务
docker-compose up -d

# 4. 访问应用
# 前端：http://localhost:3000
# 后端 API: http://localhost:5100
```

### 方式二：本地开发

```bash
# 1. 安装 Python 依赖
pip install -r backend/requirements.txt

# 2. 安装前端依赖
cd frontend-new && npm install

# 3. 启动后端服务
cd backend && flask run --port 5100

# 4. 启动前端开发服务器
cd ../frontend-new && npm run dev
```

详细部署指南请查看 [`QUICKSTART.md`](QUICKSTART.md)

---

## 📊 数据源覆盖

### 财经商业（11 个）
华尔街见闻、财联社、格隆汇、雪球、金十数据、36 氪、虎嗅、投资界、创业邦、铅笔道、清科研究

### 综合新闻（10 个）
今日头条、百度热搜、澎湃新闻、凤凰网、参考消息、腾讯新闻、新浪财经、网易财经、东方财富、和讯网

### 科技创投（12 个）
IT 之家、掘金、GitHub Trending、Hacker News、V2EX、ProductHunt、TechCrunch、36Kr、芥末圈、少数派

### 社交舆情（7 个）
微博、抖音、B 站、知乎、小红书、虎扑、贴吧

**完整数据源列表请查看 [`config/config.yaml`](config/config.yaml)**

---

## 🔌 核心 API

### 资讯相关
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/news/hot` | GET | 获取热门资讯 |
| `/api/news/recommend` | GET | 个性化推荐 |
| `/api/news/analysis` | GET | AI 分析报告 |

### 知识图谱
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/graph/nodes` | GET | 获取图谱节点 |
| `/api/graph/relations` | GET | 获取关系网络 |
| `/api/graph/query` | POST | Cypher 查询 |

### 用户系统
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/users/register` | POST | 用户注册 |
| `/api/users/interests` | POST | 更新兴趣标签 |
| `/api/users/behavior` | POST | 上报用户行为 |

完整 API 文档请查看 [`API.md`](API.md)

---

## ⚙️ 环境配置

### 环境变量

创建 `.env` 文件并配置：

```bash
# 数据库
DB_PATH=./data/database.sqlite3

# Neo4j 知识图谱
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Qwen 大模型（必填）
DASHSCOPE_API_KEY=sk-xxxxxxxx

# 管理员 Token
ADMIN_TOKEN=change-me-please
```

### 获取 Qwen API Key

1. 访问 [阿里云百炼控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录阿里云账号
3. 开通 DashScope 服务
4. 创建 API Key
5. 填入 `.env` 文件

---

## 📈 版本规划

### v1.0 (当前版本) - MVP
- ✅ 基础资讯聚合
- ✅ AI 智能分析
- ✅ 个性化推荐
- ✅ 知识图谱可视化

### v2.0 (Q2 2026) - 增强版
- 🚧 商业机会自动发现
- 🚧 竞品监控系统
- 🚧 投融资事件追踪
- 🚧 行业报告生成

### v3.0 (Q4 2026) - 企业版
- 📋 多用户团队协作
- 📋 自定义监控看板
- 📋 API 开放平台
- 📋 SaaS 化部署

---

## 🤝 参与贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 开源协议

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 👥 团队

**Lumos Team** © 2026

- GitHub: [@njndxjj](https://github.com/njndxjj)
- 项目地址：https://github.com/njndxjj/news-dashboard

---

<div align="center">

**让 Lumos 成为你商业决策的第一道光** 🌟

[阅读文档](INDEX.md) · [快速开始](QUICKSTART.md) · [API 参考](API.md)

</div>
