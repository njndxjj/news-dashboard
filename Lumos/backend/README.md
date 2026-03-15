# Lumos 后端服务

后端基于 Flask 框架，提供 RESTful API 接口，支持用户管理、新闻抓取、AI 分析、推荐系统、知识图谱等功能。

---

## 📁 目录结构

```
backend/
├── app.py                        # Flask 主应用入口
├── app_knowledge_graph.py        # 知识图谱 API
├── user_module.py                # 用户系统（登录/注册/验证码）
├── recommendation_service.py     # 推荐引擎
├── knowledge_graph.py            # Neo4j 图谱服务
├── task_scheduler.py             # 定时任务调度
├── email_notifications.py        # 邮件通知
├── subscription.py               # 订阅管理
├── realtime_service.py           # 实时推送服务
├── qwen_integration.py           # Qwen 大模型集成
├── snowflake_id.py               # 分布式 ID 生成器
├── subscription_api.py           # 订阅 API
├── data_collection.py            # 数据采集
├── data_processing.py            # 数据处理
├── contact.py                    # 联系方式 API
├── init_db.py                    # 数据库初始化
├── recommend.py                  # 推荐逻辑
├── requirements.txt              # Python 依赖
└── README.md                     # 本文档
```

---

## 🚀 快速启动

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量
创建 `.env` 文件：
```bash
DB_PATH=../database.sqlite3
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxx
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### 3. 初始化数据库
```bash
python init_db.py
```

### 4. 启动服务
```bash
# 开发模式
flask run --debug

# 生产模式
gunicorn -w 4 -b 0.0.0.0:5100 app:app
```

---

## 📡 API 接口

### 用户认证
- `POST /api/users/register` - 用户注册/游客登录
- `POST /api/users/send-code` - 发送验证码
- `POST /api/users/verify-code` - 验证验证码
- `GET /api/users/subscriptions` - 获取用户订阅
- `POST /api/users/subscriptions` - 更新订阅

### 新闻相关
- `GET /api/news/hot` - 获取热门新闻
- `GET /api/news/recommend` - 获取推荐新闻
- `GET /api/news/analysis` - 获取 AI 分析
- `GET /api/news/search` - 搜索新闻

### 知识图谱
- `GET /api/graph/nodes` - 获取节点
- `GET /api/graph/relations` - 获取关系
- `POST /api/graph/query` - Cypher 查询

### 系统管理
- `GET /api/admin/platforms` - 平台配置
- `POST /api/admin/scheduler/trigger` - 触发任务

完整 API 文档见 [API.md](../API.md)

---

## 🗄️ 数据库

### SQLite 表结构
- **Users**: 用户信息
- **InterestPoints**: 兴趣标签
- **NewsSources**: 新闻源
- **Articles**: 文章
- **UserSubscriptions**: 用户订阅
- **UserBehaviors**: 用户行为
- **NewsAnalysis**: 新闻分析结果

### Neo4j 图谱
- **Node Types**: Person, Company, Event, Topic
- **Relationship Types**: WORKS_AT, INVESTED_IN, PARTICIPATED_IN, COMPETES_WITH

---

## 🤖 AI 集成

### Qwen 大模型
```python
from qwen_integration import QwenAnalyzer

analyzer = QwenAnalyzer()
result = analyzer.analyze("新闻文本内容")

# 返回:
# {
#   "sentiment": "positive",
#   "keywords": ["AI", "大模型"],
#   "summary": "摘要内容"
# }
```

### 情感分析
- positive (正面)
- neutral (中性)
- negative (负面)

### 关键词提取
- TF-IDF 算法
- Qwen 大模型增强

---

## ⏰ 定时任务

### 任务配置
```python
# crontab_config
*/10 * * * *  python fetch_news.py       # 每 10 分钟抓取
0 */1 * * *   python analyze_news.py     # 每小时分析
0 8 * * *     python generate_report.py  # 每天 8 点生成日报
```

### 查看任务状态
```bash
python task_scheduler.py status
```

### 手动触发
```bash
python task_scheduler.py trigger fetch_news
```

---

## 🧪 测试

```bash
# 运行测试
pytest tests/ -v

# 测试覆盖率
pytest tests/ --cov=backend --cov-report=html
```

---

## 🔧 配置说明

### config.yaml
```yaml
platforms:
  - id: "toutiao"
    name: "今日头条"
  - id: "weibo"
    name: "微博"

admin:
  tokens:
    - "admin-token"
  users:
    - username: "admin"
      password: "admin123"
```

### rss_mapping.yaml
```yaml
rss_mapping:
  ithome:
    url: "https://www.ithome.com/rss/"
  hackernews:
    url: "https://news.ycombinator.com/rss"
```

---

## 📝 开发指南

### 添加新的 API
```python
# news_module.py
from flask import Blueprint, jsonify

news_bp = Blueprint('news', __name__)

@news_bp.route('/api/news/custom', methods=['GET'])
def custom_news():
    return jsonify({
        "success": True,
        "data": {"news": []}
    })
```

### 日志记录
```python
import logging

logging.info("信息日志")
logging.warning("警告日志")
logging.error("错误日志")
```

---

## 🐛 常见问题

### Q: 数据库连接失败
A: 检查 `DB_PATH` 环境变量是否正确

### Q: Qwen API 调用失败
A: 检查 `DASHSCOPE_API_KEY` 是否有效

### Q: Neo4j 连接失败
A: 检查 Neo4j 服务是否启动，端口 7687 是否开放

---

*最后更新：2026-03-15*
