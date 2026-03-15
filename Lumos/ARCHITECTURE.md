# Lumos 架构设计文档

## 1. 系统概述

### 1.1 项目背景
Lumos 是一个智能化的舆情监控与知识图谱平台，旨在帮助企业和个人实时监控全网热点新闻，通过 AI 大模型进行智能分析和个性化推荐，并以知识图谱的形式可视化展示信息之间的关联关系。

### 1.2 设计目标
- **实时性**：10 分钟级别的数据更新频率
- **智能化**：AI 驱动的内容分析和推荐
- **可视化**：直观的知识图谱展示
- **可扩展**：模块化设计，易于添加新数据源
- **高可用**：完善的错误处理和重试机制

---

## 2. 整体架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Web App    │  │  Mobile Web  │  │   Admin UI   │      │
│  │   (React)    │  │  (Responsive)│  │   Dashboard  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   REST API   │  │   Auth       │  │   Rate       │      │
│  │   (Flask)    │  │   Middleware │  │   Limiting   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   User       │  │   Recommend  │  │   Knowledge  │      │
│  │   Service    │  │   Service    │  │   Graph      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Content    │  │   Schedule   │  │   Notify     │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Access Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   SQLite     │  │   Neo4j      │  │   Redis      │      │
│  │   ORM        │  │   Driver     │  │   Cache      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Collection Layer                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   RSS        │  │   Crawler    │  │   Browser    │      │
│  │   Parser     │  │   Cluster    │  │   Search     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流架构

```
数据源 → 采集层 → 处理层 → 存储层 → 分析层 → 展示层
  │        │        │        │        │        │
  ▼        ▼        ▼        ▼        ▼        ▼
RSS     爬虫     清洗     SQLite   AI 分析   React
API     集群     去重     Neo4j   推荐     图表
```

---

## 3. 模块详细设计

### 3.1 数据采集模块 (Data Collection)

#### 3.1.1 架构图
```
┌────────────────────────────────────────────────────────────┐
│                    DataCollector                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  RSSFetcher  │  │  CrawlerMgr  │  │  BrowserCtrl │     │
│  │              │  │              │  │              │     │
│  │ - 解析 RSS   │  │ - 调度爬虫   │  │ - Playwright │     │
│  │ - 增量更新   │  │ - 限流控制   │  │ - 截图搜索   │     │
│  │ - 错误重试   │  │ - 代理轮换   │  │ - 验证码处理 │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────────────────────────────────────────┘
```

#### 3.1.2 核心类
- `BaseCrawler`: 爬虫基类，定义通用接口
- `RSSFetcher`: RSS 源解析器
- `CrawlerManager`: 爬虫集群管理器
- `BrowserController`: 浏览器自动化工具

#### 3.1.3 数据源分类
| 类型 | 数量 | 获取方式 |
|------|------|----------|
| RSS 源 | 25+ | feedparser 解析 |
| API 接口 | 15+ | HTTP 请求 |
| 网页爬虫 | 20+ | BeautifulSoup |
| 浏览器自动化 | 5+ | Playwright |

---

### 3.2 数据处理模块 (Data Processing)

#### 3.2.1 处理流程
```
原始新闻 → 清洗 → 去重 → 分类 → 标签化 → 入库
   │        │      │      │      │       │
   ▼        ▼      ▼      ▼      ▼       ▼
HTML     去除    MD5    行业    关键词   SQLite
提取     噪声    比对    分类    提取    Neo4j
```

#### 3.2.2 去重算法
```python
def deduplicate(news_list):
    # 1. URL 去重
    unique_urls = set()

    # 2. 标题相似度去重（Jaccard）
    unique_titles = []
    for news in news_list:
        if news['url'] not in unique_urls:
            if not is_similar_title(news['title'], unique_titles):
                unique_titles.append(news['title'])
                unique_urls.add(news['url'])

    return unique_urls
```

---

### 3.3 AI 分析模块 (AI Analysis)

#### 3.3.1 Qwen 大模型集成
```python
class QwenAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('DASHSCOPE_API_KEY')
        self.model = 'qwen-max'

    def analyze(self, text):
        # 情感分析
        sentiment = self.analyze_sentiment(text)

        # 关键词提取
        keywords = self.extract_keywords(text)

        # 摘要生成
        summary = self.generate_summary(text)

        return {
            'sentiment': sentiment,
            'keywords': keywords,
            'summary': summary
        }
```

#### 3.3.2 分析维度
1. **情感分析**: positive / neutral / negative
2. **关键词提取**: TF-IDF + 大模型
3. **摘要生成**: 提取式 + 生成式
4. **实体识别**: 人物 / 机构 / 地点 / 事件
5. **关系抽取**: 投资 / 竞争 / 合作

---

### 3.4 推荐系统模块 (Recommendation)

#### 3.4.1 推荐策略
```
┌────────────────────────────────────────────────────────────┐
│                  RecommendationEngine                       │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │  Content-Based  │  │  Collaborative  │                 │
│  │  Filtering      │  │  Filtering      │                 │
│  │                 │  │                 │                 │
│  │ - 标签匹配      │  │ - 用户相似度     │                 │
│  │ - TF-IDF 权重   │  │ - 矩阵分解       │                 │
│  │ - 余弦相似度    │  │ - 隐式反馈       │                 │
│  └─────────────────┘  └─────────────────┘                 │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │  Hot Ranking    │  │  Hybrid         │                 │
│  │                 │  │  Ensemble       │                 │
│  │ - 时间衰减      │  │                 │                 │
│  │ - 热度计算      │  │ - 加权融合       │                 │
│  │ - 趋势预测      │  │ - 多样性控制     │                 │
│  └─────────────────┘  └─────────────────┘                 │
└────────────────────────────────────────────────────────────┘
```

#### 3.4.2 推荐公式
```
score = w1 * content_score + w2 * collaborative_score + w3 * hot_score

其中:
- content_score = cosine_similarity(user_keywords, news_keywords)
- collaborative_score = pearson(user_behavior, similar_users)
- hot_score = log(view_count + 1) * time_decay
```

---

### 3.5 知识图谱模块 (Knowledge Graph)

#### 3.5.1 图谱 Schema
```
┌────────────────────────────────────────────────────────────┐
│                      Neo4j Schema                          │
│                                                             │
│  Node Types:                                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │ Person  │  │Company  │  │ Event   │  │ Topic   │      │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
│                                                             │
│  Relationship Types:                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │ WORKS_AT │  │INVESTED_IN│  │PARTICIPATED│              │
│  │ COMPETES │  │RELATED_TO│  │MENTIONED │                │
│  └──────────┘  └──────────┘  └──────────┘                │
└────────────────────────────────────────────────────────────┘
```

#### 3.5.2 查询示例
```cypher
// 查询某公司投资的企业
MATCH (c:Company {name: '某公司'})-[:INVESTED_IN]->(target)
RETURN target.name, target.industry

// 查询人物关系网络
MATCH (p:Person)-[:WORKS_AT|PARTICIPATED_IN*2]-(related)
WHERE p.name = '某人物'
RETURN p, related
```

---

### 3.6 用户系统模块 (User System)

#### 3.6.1 数据库表结构
```sql
-- 用户表
CREATE TABLE Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    unique_id TEXT UNIQUE,
    is_guest BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 兴趣标签表
CREATE TABLE InterestPoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    parent_id INTEGER
);

-- 用户订阅表
CREATE TABLE UserSubscriptions (
    user_id INTEGER,
    keyword TEXT,
    category TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES Users(id)
);

-- 用户行为表
CREATE TABLE UserBehaviors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    news_id INTEGER,
    timestamp TIMESTAMP,
    metadata TEXT
);
```

#### 3.6.2 认证流程
```
用户登录/注册
    │
    ▼
发送验证码 (手机号)
    │
    ▼
验证验证码
    │
    ▼
生成 unique_id (Snowflake)
    │
    ▼
返回 Token (本地存储)
    │
    ▼
后续请求携带 Token
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
*/10 * * * *  python fetch_news.py       # 每 10 分钟抓取新闻
0 */1 * * *   python analyze_news.py     # 每小时分析一次
0 8 * * *     python generate_report.py  # 每天 8 点生成日报
```

---

### 3.8 前端模块 (Frontend)

#### 3.8.1 组件架构
```
App.jsx (根组件)
├── Header (导航栏)
├── LoginModal (登录弹窗)
├── MainContent (主内容区)
│   ├── HotNews (热门新闻)
│   ├── AIAnalysis (AI 分析)
│   ├── Recommendation (推荐)
│   ├── KnowledgeGraph (知识图谱)
│   └── UserInterests (兴趣管理)
├── UserBehaviorDashboard (用户行为面板)
└── ToastContainer (通知容器)
```

#### 3.8.2 状态管理
```jsx
// 使用 React Hooks 进行状态管理
const [isLoggedIn, setIsLoggedIn] = useState(false);
const [uniqueId, setUniqueId] = useState(null);
const [keywords, setKeywords] = useState([]);
const [news, setNews] = useState([]);
const [insights, setInsights] = useState(null);

// 使用 useEffect 处理副作用
useEffect(() => {
  // 页面加载时检查登录状态
  const storedId = localStorage.getItem('unique_id');
  if (storedId) {
    setUniqueId(storedId);
    setIsLoggedIn(true);
  }
}, []);
```

---

## 4. 数据库设计

### 4.1 SQLite 表结构

```sql
-- 核心表结构
Users                 -- 用户信息
InterestPoints        -- 兴趣标签
NewsSources           -- 新闻源
Articles              -- 文章
UserSubscriptions     -- 用户订阅
UserBehaviors         -- 用户行为
NewsAnalysis          -- 新闻分析结果
Recommendations       -- 推荐记录
ScheduledTasks        -- 定时任务
SystemLogs            -- 系统日志
```

### 4.2 Neo4j 节点关系

```
(:Person)-[:WORKS_AT]->(:Company)
(:Person)-[:PARTICIPATED_IN]->(:Event)
(:Company)-[:INVESTED_IN]->(:Company)
(:Company)-[:COMPETES_WITH]->(:Company)
(:Article)-[:MENTIONS]->(:Person)
(:Article)-[:ABOUT]->(:Topic)
```

---

## 5. 安全性设计

### 5.1 认证与授权
- **验证码机制**: 防止恶意注册
- **Token 验证**: API 访问控制
- **防重复点击**: 前端按钮保护
- **频率限制**: 防止 API 滥用

### 5.2 数据安全
- **输入验证**: 防止 SQL 注入
- **XSS 防护**: 前端内容转义
- **CORS 配置**: 跨域访问控制
- **敏感数据加密**: 密码/Token 加密存储

---

## 6. 性能优化

### 6.1 缓存策略
```python
# Redis 缓存配置
CACHE_CONFIG = {
    'news_list': {'ttl': 600},      # 新闻列表 10 分钟
    'user_profile': {'ttl': 3600},  # 用户画像 1 小时
    'recommendation': {'ttl': 1800} # 推荐结果 30 分钟
}
```

### 6.2 数据库优化
- **索引**: 常用查询字段建立索引
- **分页**: 大数据集分页查询
- **连接池**: 数据库连接复用

### 6.3 前端优化
- **懒加载**: 组件按需加载
- **虚拟滚动**: 长列表优化
- **防抖节流**: 频繁操作优化

---

## 7. 监控与日志

### 7.1 监控指标
- **系统层面**: CPU、内存、磁盘
- **应用层面**: QPS、响应时间、错误率
- **业务层面**: 用户活跃度、新闻抓取量、推荐点击率

### 7.2 日志规范
```python
import logging

# 日志级别
logging.DEBUG     # 调试信息
logging.INFO      # 运行信息
logging.WARNING   # 警告信息
logging.ERROR     # 错误信息
logging.CRITICAL  # 严重错误

# 日志格式
"%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## 8. 部署架构

### 8.1 Docker 部署
```yaml
version: '3.8'
services:
  backend:
    build: ./
    ports:
      - "5100:5100"
    volumes:
      - ./data:/app/data
    environment:
      - DB_PATH=/app/data/database.sqlite3

  frontend:
    image: node:16
    working_dir: /app
    volumes:
      - ./frontend:/app
    command: npm start
    ports:
      - "3000:3000"

  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
```

### 8.2 生产环境建议
- **负载均衡**: Nginx 反向代理
- **SSL 证书**: HTTPS 加密
- **CDN**: 静态资源加速
- **数据库备份**: 定期自动备份

---

## 9. 扩展性设计

### 9.1 新增数据源
1. 在 `config.yaml` 添加配置
2. 实现 `BaseCrawler` 子类
3. 注册到采集器

### 9.2 新增分析模型
1. 实现分析器接口
2. 配置 API Key
3. 更新分析管道

### 9.3 新增推荐策略
1. 实现推荐算法
2. 配置权重参数
3. A/B 测试验证

---

## 10. 未来规划

### 短期目标 (Q1 2026)
- [ ] 支持更多数据源 (100+)
- [ ] 优化推荐算法准确率
- [ ] 移动端 App 开发

### 中期目标 (Q2 2026)
- [ ] 多语言支持
- [ ] 企业级权限管理
- [ ] API 开放平台

### 长期目标 (2026 全年)
- [ ] SaaS 化部署
- [ ] 自定义仪表盘
- [ ] AI 预测分析

---

*最后更新：2026-03-15*
