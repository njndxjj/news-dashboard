# Lumos 架构设计文档

## 1. 系统概述

### 1.1 项目背景

**Lumos**（拉丁语意为"光"）是一个面向中小企业主的智能化商业洞察系统，旨在帮助企业家在复杂多变的商业环境中捕捉机会、洞察趋势、做出明智决策。

在信息爆炸的时代，中小企业主面临着：
- 海量信息难以筛选，错过重要商机
- 缺乏有效的竞争情报收集手段
- 决策缺乏数据支撑，凭经验判断
- 时间有限，无法持续关注行业动态

Lumos 通过 AI 驱动的数据采集、智能分析和个性化推荐，成为每个中小企业主的"首席情报官"。

### 1.2 设计目标

| 目标 | 描述 |
|------|------|
| **商业敏感** | 10 分钟级数据更新，不错过任何重要商机 |
| **AI 驱动** | 通义千问大模型智能分析，提取商业洞察 |
| **千人千面** | 基于用户兴趣图谱的个性化推荐 |
| **关系洞察** | Neo4j 知识图谱揭示商业实体关联 |
| **简单可靠** | 开箱即用，完善的错误处理和重试机制 |

---

## 2. 整体架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ React Web   │ │ Mobile Web  │ │ Admin Dash  │           │
│  │ 商家洞察首页 │ │ 响应式适配  │ │ 管理后台    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API 服务层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Flask REST  │ │ JWT Auth    │ │ Rate Limit  │           │
│  │ API Gateway │ │ 身份认证    │ │ 频率限制    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      业务服务层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 推荐引擎    │ │ 知识图谱    │ │ 用户系统    │           │
│  │ 商业机会推荐 │ │ Neo4j 关系  │ │ 兴趣图谱    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ AI 分析     │ │ 定时调度    │ │ 通知服务    │           │
│  │ 摘要/情感   │ │ 10 分钟更新  │ │ 飞书/邮件   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据采集层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ RSS Parser  │ │ Crawler     │ │ Browser     │           │
│  │ 25+ RSS 源   │ │ 60+ 爬虫    │ │ Playwright  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ SQLite      │ │ Neo4j       │ │ Redis       │           │
│  │ 业务数据    │ │ 知识图谱    │ │ 缓存层      │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流架构

```
商业数据源 → 采集层 → 处理层 → 存储层 → 分析层 → 推荐层 → 展示层
   │          │        │        │        │        │        │
   ▼          ▼        ▼        ▼        ▼        ▼        ▼
财经/科技   爬虫     清洗     SQLite  Qwen   兴趣匹配  React
RSS/API    集群     去重     Neo4j   分析   协同过滤  图表
```

---

## 3. 模块详细设计

### 3.1 数据采集模块 (Data Collection)

#### 3.1.1 数据源分类

| 类型 | 数量 | 获取方式 | 覆盖领域 |
|------|------|----------|----------|
| RSS 源 | 25+ | feedparser | 财经、科技、创投 |
| API 接口 | 15+ | HTTP 请求 | 热搜榜、实时热点 |
| 网页爬虫 | 20+ | BeautifulSoup | 新闻媒体、行业资讯 |

#### 3.1.2 核心组件

- **`BaseCrawler`**: 爬虫基类，定义通用接口和重试机制
- **`RSSFetcher`**: RSS 源解析器，支持增量更新
- **`CrawlerManager`**: 爬虫集群管理器，负责任务调度和限流
- **`BrowserController`**: Playwright 浏览器自动化，处理动态页面

#### 3.1.3 数据源配置

在 `config/config.yaml` 中配置：

```yaml
sources:
  finance:
    - name: 华尔街见闻
      url: https://wallstreetcn.com
      type: rss
      enabled: true

    - name: 36 氪
      url: https://36kr.com
      type: crawler
      enabled: true

  technology:
    - name: IT 之家
      url: https://ithome.com
      type: crawler
      enabled: true
```

---

### 3.2 数据处理模块 (Data Processing)

#### 3.2.1 处理流程

```
原始新闻 → 清洗 → 去重 → 分类 → 标签化 → 商业实体识别 → 入库
   │        │      │      │      │         │            │
   ▼        ▼      ▼      ▼      ▼         ▼            ▼
HTML     去除    MD5   行业    关键词    公司/人物    SQLite
提取     噪声    比对   分类    提取      产品识别     Neo4j
```

#### 3.2.2 商业实体识别

使用 Qwen 大模型识别新闻中的商业实体：

```python
def extract_business_entities(text):
    """提取商业实体：公司、人物、产品、投资事件"""
    prompt = f"""
    从以下新闻中提取商业实体：
    - 公司名称
    - 关键人物（CEO、创始人等）
    - 产品/服务
    - 投资事件（融资金额、轮次、投资方）

    新闻内容：{text}
    """
    response = qwen_client.generate(prompt)
    return parse_entities(response)
```

---

### 3.3 AI 分析模块 (AI Analysis)

#### 3.3.1 Qwen 大模型集成

```python
class QwenAnalyzer:
    """通义千问分析器"""

    def __init__(self):
        self.api_key = os.getenv('DASHSCOPE_API_KEY')
        self.model = 'qwen-max'

    def analyze(self, news):
        """多维度分析"""
        return {
            'summary': self.generate_summary(news),       # 摘要
            'sentiment': self.analyze_sentiment(news),    # 情感
            'entities': self.extract_entities(news),      # 实体
            'keywords': self.extract_keywords(news),      # 关键词
            'insights': self.generate_insights(news)      # 商业洞察
        }
```

#### 3.3.2 分析维度

| 维度 | 说明 | 输出 |
|------|------|------|
| **摘要生成** | 提炼新闻核心要点 | 100-200 字摘要 |
| **情感分析** | 正面/负面/中性 | sentiment_score |
| **实体识别** | 公司/人物/产品 | 结构化实体列表 |
| **关键词提取** | TF-IDF + 大模型 | 关键词及权重 |
| **商业洞察** | 机会/风险/趋势 | 洞察建议 |

---

### 3.4 推荐系统模块 (Recommendation)

#### 3.4.1 推荐架构

```
┌────────────────────────────────────────────────────────────┐
│                  Lumos 推荐引擎                              │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │  基于内容推荐   │  │  协同过滤       │                 │
│  │  Content-Based  │  │  Collaborative  │                 │
│  │                 │  │                 │                 │
│  │ - 兴趣标签匹配  │  │ - 相似用户行为  │                 │
│  │ - 关键词权重    │  │ - 矩阵分解      │                 │
│  │ - TF-IDF 相似度 │  │ - 隐式反馈      │                 │
│  └─────────────────┘  └─────────────────┘                 │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │  热门度计算     │  │  混合集成       │                 │
│  │  Hot Ranking    │  │  Hybrid         │                 │
│  │                 │  │                 │                 │
│  │ - 时间衰减      │  │ - 加权融合      │                 │
│  │ - 热度趋势      │  │ - 多样性控制    │                 │
│  │ - 传播速度      │  │ - 新颖性平衡    │                 │
│  └─────────────────┘  └─────────────────┘                 │
└────────────────────────────────────────────────────────────┘
```

#### 3.4.2 推荐公式

```
最终得分 = w1 × 内容匹配度 + w2 × 协同过滤分 + w3 × 热门度 + w4 × 新颖度

其中:
- 内容匹配度 = cosine(user_vector, news_vector)
- 协同过滤分 = Pearson(相似用户行为)
- 热门度 = log(阅读量 + 1) × time_decay
- 新颖度 = 1 / (用户已接触同类新闻数 + 1)
```

#### 3.4.3 用户兴趣向量构建

```python
def build_user_vector(user_id):
    """从用户兴趣图谱构建向量"""
    interests = get_user_interests(user_id, limit=100)

    vector = {}
    for interest in interests:
        keyword = interest['entity_name']
        weight = interest['current_weight']  # 考虑时间衰减
        vector[keyword] = weight

    return vector
```

---

### 3.5 知识图谱模块 (Knowledge Graph)

#### 3.5.1 图谱 Schema 设计

```
Neo4j 节点类型:
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ Company │  │ Person  │  │ Product │  │ Event   │
│ 公司    │  │ 人物    │  │ 产品    │  │ 事件    │
└─────────┘  └─────────┘  └─────────┘  └─────────┘

关系类型:
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ INVESTED_IN  │  │ COMPETES_WITH│  │ PARTNERSHIP  │
│ 投资         │  │ 竞争         │  │ 合作         │
└──────────────┘  └──────────────┘  └──────────────┘
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ WORKS_AT     │  │ FOUNDED_BY   │  │ ACQUIRED_BY  │
│ 任职         │  │ 创立         │  │ 被收购       │
└──────────────┘  └──────────────┘  └──────────────┘
```

#### 3.5.2 典型查询场景

```cypher
// 查询某公司的投资版图
MATCH (c:Company {name: '某公司'})-[:INVESTED_IN*1..3]->(target)
RETURN c.name, target.name, target.industry, target.funding_round

// 查找竞争关系网络
MATCH (c:Company {name: '某公司'})-[:COMPETES_WITH]-(competitor)
RETURN c.name, competitor.name, competitor.market_share

// 发现人物关系链
MATCH (p:Person {name: '某人物'})-[:WORKS_AT|FOUNDED_BY*1..2]-(org)
RETURN p.name, org.name, org.type
```

---

### 3.6 用户系统模块 (User System)

#### 3.6.1 用户画像

```
用户画像
├── 基础信息
│   ├── unique_id (Snowflake 算法生成)
│   ├── 注册时间
│   └── 用户类型 (游客/注册用户/管理员)
│
├── 兴趣图谱
│   ├── 关键词权重
│   ├── 行业偏好
│   ├── 公司关注列表
│   └── 人物关注列表
│
├── 行为记录
│   ├── 点击历史
│   ├── 收藏记录
│   ├── 分享行为
│   └── 搜索记录
│
└── 推荐反馈
    ├── 点击率
    ├── 停留时长
    └── 满意度评分
```

#### 3.6.2 数据库表结构

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unique_id TEXT UNIQUE NOT NULL,
    username TEXT,
    phone TEXT,
    is_guest BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 兴趣图谱表
CREATE TABLE user_interest_graph (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,  -- keyword/company/person/product
    entity_name TEXT NOT NULL,
    relation_type TEXT NOT NULL, -- click/like/collect/search
    weight REAL DEFAULT 1.0,
    current_weight REAL,
    last_action_at TEXT,
    UNIQUE(user_id, entity_type, entity_name, relation_type)
);

-- 用户行为表
CREATE TABLE user_behaviors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    news_id INTEGER,
    stay_duration INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 3.7 定时任务模块 (Scheduler)

#### 3.7.1 任务调度架构

```
┌────────────────────────────────────────────────────────────┐
│                    TaskScheduler                            │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │  Cron Parser    │  │  Task Queue     │                 │
│  │                 │  │                 │                 │
│  │ - Cron 表达式   │  │ - 优先级队列     │                 │
│  │ - 周期解析      │  │ - 任务去重       │                 │
│  └─────────────────┘  └─────────────────┘                 │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │  Worker Pool    │  │  Monitor        │                 │
│  │                 │  │                 │                 │
│  │ - 并发控制      │  │ - 状态追踪       │                 │
│  │ - 失败重试      │  │ - 日志记录       │                 │
│  └─────────────────┘  └─────────────────┘                 │
└────────────────────────────────────────────────────────────┘
```

#### 3.7.2 定时任务配置

```yaml
# crontab_config
*/10 * * * *   fetch_news          # 每 10 分钟抓取最新新闻
0 * * * *      analyze_news        # 每小时分析一次
0 2 * * *      apply_decay         # 每天 2 点应用兴趣衰减
0 8 * * *      generate_daily      # 每天 8 点生成日报
```

---

### 3.8 前端模块 (Frontend)

#### 3.8.1 组件架构

```
App.jsx
├── Header (导航栏)
│   ├── Logo
│   ├── Navigation
│   └── UserMenu
│
├── MainContent
│   ├── HotNews (热门资讯)
│   ├── Recommendation (个性化推荐)
│   ├── AIAnalysis (AI 分析面板)
│   ├── KnowledgeGraph (知识图谱)
│   └── UserInterests (兴趣管理)
│
├── Sidebar
│   ├── TrendingTopics (热门话题)
│   ├── FollowedCompanies (关注公司)
│   └── QuickActions (快捷操作)
│
└── Footer
```

#### 3.8.2 状态管理

```jsx
// 使用 React Hooks 进行状态管理
const [isLoggedIn, setIsLoggedIn] = useState(false);
const [uniqueId, setUniqueId] = useState(null);
const [news, setNews] = useState([]);
const [recommendations, setRecommendations] = useState([]);
const [interests, setInterests] = useState([]);

// 使用 useEffect 处理数据获取
useEffect(() => {
  fetchNews();
  fetchRecommendations();
}, [uniqueId]);
```

---

## 4. 安全性设计

### 4.1 认证与授权

| 机制 | 说明 |
|------|------|
| **验证码** | 防止恶意注册和 API 滥用 |
| **Token 验证** | JWT Token 用于 API 访问控制 |
| **防重复点击** | 前端按钮 debounce 保护 |
| **频率限制** | 基于 IP 和用户的 API 限流 |

### 4.2 数据安全

- **输入验证**: 防止 SQL 注入和 XSS 攻击
- **CORS 配置**: 严格的跨域访问控制
- **敏感数据加密**: 密码和 Token 加密存储
- **备份机制**: 数据库定期自动备份

---

## 5. 性能优化

### 5.1 缓存策略

```python
CACHE_CONFIG = {
    'news_hot': {'ttl': 600},       # 热门新闻 10 分钟
    'recommendation': {'ttl': 1800}, # 推荐结果 30 分钟
    'user_profile': {'ttl': 3600},   # 用户画像 1 小时
    'graph_query': {'ttl': 900},     # 图谱查询 15 分钟
}
```

### 5.2 数据库优化

- **索引设计**: 常用查询字段建立索引
- **分页查询**: 大数据集分页处理
- **连接池**: 数据库连接复用

### 5.3 前端优化

- **懒加载**: 组件按需加载
- **虚拟滚动**: 长列表性能优化
- **防抖节流**: 频繁操作优化

---

## 6. 监控与日志

### 6.1 监控指标

| 类别 | 指标 |
|------|------|
| **系统** | CPU、内存、磁盘、网络 |
| **应用** | QPS、响应时间、错误率 |
| **业务** | 日活用户、新闻抓取量、推荐点击率 |

### 6.2 日志规范

```python
# 日志级别
logging.DEBUG     # 调试信息
logging.INFO      # 运行信息
logging.WARNING   # 警告
logging.ERROR     # 错误
logging.CRITICAL  # 严重错误

# 日志格式
"%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## 7. 部署架构

### 7.1 Docker Compose 配置

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5100:5100"
    volumes:
      - ./data:/app/data
    environment:
      - DB_PATH=/app/data/database.sqlite3
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}

  frontend:
    build: ./frontend-new
    ports:
      - "3000:80"
    depends_on:
      - backend

  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
```

### 7.2 生产环境建议

- **负载均衡**: Nginx 反向代理
- **SSL 证书**: HTTPS 加密传输
- **CDN 加速**: 静态资源 CDN 分发
- **数据库备份**: 每日自动备份到云存储

---

## 8. 扩展性设计

### 8.1 新增数据源

1. 在 `config/config.yaml` 添加配置
2. 继承 `BaseCrawler` 实现爬虫类
3. 注册到数据采集模块

### 8.2 新增 AI 模型

1. 实现分析器接口
2. 配置 API Key
3. 更新分析管道

### 8.3 新增推荐策略

1. 实现推荐算法
2. 配置权重参数
3. A/B 测试验证

---

## 9. 版本历史

### v1.0 (2026-03) - MVP
- ✅ 基础资讯聚合
- ✅ AI 智能分析
- ✅ 个性化推荐
- ✅ 知识图谱可视化

### v2.0 (2026-Q2) - 增强版 (规划)
- 🚧 商业机会自动发现
- 🚧 竞品监控系统
- 🚧 投融资事件追踪

### v3.0 (2026-Q4) - 企业版 (规划)
- 📋 多用户团队协作
- 📋 自定义监控看板
- 📋 API 开放平台

---

*最后更新：2026-03-15*

*Lumos Team © 2026*
