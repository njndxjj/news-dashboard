# Lumos API 接口文档

本文档详细描述了 Lumos 商家洞察系统提供的所有 REST API 接口。

---

## 📡 基础信息

### API 地址
| 环境 | 地址 |
|------|------|
| **开发环境** | `http://localhost:5100/api` |
| **生产环境** | `https://your-domain.com/api` |

### 通用响应格式
```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": 1773548000662
}
```

### 错误响应
```json
{
  "success": false,
  "error": "错误信息",
  "error_code": "ERROR_CODE",
  "timestamp": 1773548000662
}
```

### 认证方式
大部分接口需要在 Header 中携带用户 ID:
```
Authorization: Bearer <unique_id>
```

---

## 🔐 用户认证 API

### 1. 发送验证码
**POST** `/api/users/send-code`

**请求体**:
```json
{
  "phone": "13800138000"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "message": "验证码已发送",
    "mock_code": "123456"
  }
}
```

**说明**:
- 验证码有效期 5 分钟
- 生产环境应集成短信服务商 API

---

### 2. 验证验证码
**POST** `/api/users/verify-code`

**请求体**:
```json
{
  "phone": "13800138000",
  "code": "123456"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "message": "验证码验证成功"
  }
}
```

---

### 3. 用户注册/登录
**POST** `/api/users/register`

**请求体**:
```json
{
  "username": "张三",
  "phone": "13800138000",
  "email": "zhangsan@example.com",
  "verification_code": "123456",
  "keywords": "AI，创业，融资"
}
```

**游客模式请求体**:
```json
{
  "username": "Guest",
  "phone": "",
  "keywords": ""
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "unique_id": "1234567890123456789",
    "username": "张三",
    "is_guest": false,
    "keywords": ["AI", "创业", "融资"]
  }
}
```

---

### 4. 获取用户订阅
**GET** `/api/users/subscriptions?user_id=<unique_id>`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "user_id": "1234567890123456789",
    "keywords": ["AI", "大模型", "创业"],
    "is_default": false,
    "categories": ["科技领域"]
  }
}
```

---

### 5. 更新用户订阅
**POST** `/api/users/subscriptions`

**请求体**:
```json
{
  "user_id": "1234567890123456789",
  "keywords": ["AI", "创业", "融资"],
  "categories": ["科技领域"]
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "message": "订阅已更新"
  }
}
```

---

### 6. 获取预设兴趣标签
**GET** `/api/users/interests`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "categories": {
      "科技领域": ["创业", "startups", "融资", "AI"],
      "宏观政策": ["政策", "法规", "监管"],
      "行业趋势": ["数字化", "智能化", "转型"]
    }
  }
}
```

---

## 📰 新闻相关 API

### 1. 获取热门新闻
**GET** `/api/news/hot?limit=20&platform=toutiao`

**参数**:
- `limit`: 返回数量，默认 20
- `platform`: 平台筛选，可选

**响应示例**:
```json
{
  "success": true,
  "data": {
    "news": [
      {
        "id": 1,
        "title": "AI 大模型竞争白热化，多家厂商发布新产品",
        "source": "36Kr",
        "url": "https://example.com/news/1",
        "published": "2026-03-15 10:00",
        "hot_score": 95,
        "sentiment": "positive",
        "keywords": ["AI", "大模型"],
        "summary": "多家 AI 厂商今日发布新一代大模型产品..."
      }
    ],
    "total": 100,
    "update_time": "2026-03-15 12:00"
  }
}
```

---

### 2. 获取推荐新闻
**GET** `/api/news/recommend?user_id=<unique_id>&limit=20`

**参数**:
- `user_id`: 用户 ID
- `limit`: 返回数量，默认 20

**响应示例**:
```json
{
  "success": true,
  "data": {
    "news": [
      {
        "id": 2,
        "title": "某公司完成 B 轮融资，估值超 10 亿美元",
        "source": "虎嗅",
        "url": "https://example.com/news/2",
        "published": "2026-03-15 09:30",
        "recommend_reason": "与你关注的\"创业\"相关"
      }
    ],
    "algorithm": "hybrid",
    "update_time": "2026-03-15 12:00"
  }
}
```

---

### 3. 获取 AI 分析结果
**GET** `/api/news/analysis?news_id=1`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "news_id": 1,
    "sentiment": {
      "label": "positive",
      "confidence": 0.92
    },
    "keywords": ["AI", "大模型", "产品发布"],
    "summary": "多家 AI 厂商今日发布新一代大模型产品，行业竞争进一步加剧...",
    "entities": [
      {"name": "某公司", "type": "Organization"},
      {"name": "张三", "type": "Person"}
    ]
  }
}
```

---

### 4. 搜索新闻
**GET** `/api/news/search?q=AI&platform=toutiao&start_date=2026-03-01`

**参数**:
- `q`: 搜索关键词
- `platform`: 平台筛选
- `start_date`: 开始日期
- `end_date`: 结束日期
- `limit`: 返回数量

**响应示例**:
```json
{
  "success": true,
  "data": {
    "news": [],
    "total": 50,
    "query": "AI"
  }
}
```

---

## 🕸️ 知识图谱 API

### 1. 获取图谱节点
**GET** `/api/graph/nodes?keyword=AI`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "nodes": [
      {
        "id": "n1",
        "name": "某公司",
        "type": "Company",
        "properties": {
          "industry": "人工智能",
          "founded": "2020"
        }
      },
      {
        "id": "n2",
        "name": "张三",
        "type": "Person",
        "properties": {
          "title": "CEO"
        }
      }
    ]
  }
}
```

---

### 2. 获取关系网络
**GET** `/api/graph/relations?node_id=n1`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "relations": [
      {
        "source": "n1",
        "target": "n2",
        "type": "WORKS_AT",
        "properties": {
          "since": "2020"
        }
      }
    ]
  }
}
```

---

### 3. Cypher 查询
**POST** `/api/graph/query`

**请求体**:
```json
{
  "query": "MATCH (c:Company)-[:INVESTED_IN]->(t) RETURN c.name, t.name"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "results": [
      {"c.name": "某公司", "t.name": "被投公司"}
    ]
  }
}
```

---

## ⚙️ 系统管理 API

### 1. 获取平台配置
**GET** `/api/admin/platforms`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "platforms": [
      {"id": "toutiao", "name": "今日头条", "enabled": true},
      {"id": "weibo", "name": "微博", "enabled": false}
    ]
  }
}
```

---

### 2. 更新平台配置
**POST** `/api/admin/platforms`

**请求体**:
```json
{
  "platform_id": "weibo",
  "enabled": true
}
```

---

### 3. 获取定时任务状态
**GET** `/api/admin/scheduler`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "name": "fetch_news",
        "cron": "*/10 * * * *",
        "last_run": "2026-03-15 12:00",
        "status": "success"
      }
    ]
  }
}
```

---

### 4. 手动触发任务
**POST** `/api/admin/scheduler/trigger`

**请求体**:
```json
{
  "task_name": "fetch_news"
}
```

---

## 📊 用户行为分析 API

### 1. 上报用户行为
**POST** `/api/behavior/track`

**请求体**:
```json
{
  "user_id": "1234567890123456789",
  "action": "click",
  "news_id": 1,
  "metadata": {
    "position": "recommend_list",
    "duration": 30
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "message": "行为已记录"
  }
}
```

---

### 2. 获取用户行为统计
**GET** `/api/behavior/stats?user_id=<unique_id>`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_views": 100,
    "total_clicks": 50,
    "favorite_categories": ["科技领域", "财经"],
    "active_hours": [9, 10, 14, 20]
  }
}
```

---

## 🔧 开发工具 API

### 1. 健康检查
**GET** `/api/health`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 86400
  }
}
```

---

### 2. 获取 API 文档
**GET** `/api/docs`

返回 Swagger/OpenAPI 格式的文档。

---

## 📝 错误码说明

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权访问 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 503 | 服务暂时不可用 |

---

## 🔒 安全建议

1. **生产环境必须启用 HTTPS**
2. **管理员接口需要 Token 认证**
3. **敏感操作需要二次验证**
4. **实施 API 限流策略**
5. **定期更新 API Key**

---

## 📚 使用示例

### JavaScript (Fetch)
```javascript
// 获取热门新闻
const response = await fetch('http://localhost:5100/api/news/hot?limit=10');
const data = await response.json();
console.log(data.data.news);

// 用户注册
const registerResponse = await fetch('http://localhost:5100/api/users/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'Test User',
    phone: '',
    keywords: 'AI，创业'
  })
});
const registerData = await registerResponse.json();
localStorage.setItem('unique_id', registerData.data.unique_id);
```

### Python (Requests)
```python
import requests

# 获取热门新闻
response = requests.get('http://localhost:5100/api/news/hot', params={'limit': 10})
news_list = response.json()['data']['news']

# 用户注册
register_data = {
    'username': 'Test User',
    'phone': '',
    'keywords': 'AI，创业'
}
response = requests.post('http://localhost:5100/api/users/register', json=register_data)
unique_id = response.json()['data']['unique_id']
```

---

*Lumos Team © 2026*
*最后更新：2026-03-15*
