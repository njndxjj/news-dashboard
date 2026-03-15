# Lumos 开发人员指南

本文档面向 Lumos 项目的开发者，介绍开发环境搭建、代码规范、调试技巧等信息。

---

## 🛠️ 开发环境搭建

### 1. 克隆项目
```bash
git clone https://github.com/njndxjj/lumos.git
cd Lumos
```

### 2. Python 环境
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r backend/requirements.txt
pip install pytest pytest-cov  # 测试工具
pip install black flake8 mypy  # 代码质量工具
```

### 3. Node.js 环境
```bash
cd frontend-new

# 安装依赖
npm install

# 安装开发工具
npm install -D @types/node prettier eslint
```

### 4. 数据库初始化
```bash
# SQLite
python database_init.py

# Neo4j (可选)
# 使用 Docker 启动
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

---

## 📝 代码规范

### Python 规范

遵循 PEP 8 规范，使用以下工具检查：

```bash
# 代码格式化
black backend/

# 代码检查
flake8 backend/

# 类型检查
mypy backend/
```

**命名规范**:
```python
# 变量和函数：小写 + 下划线
def fetch_news_data():
    news_list = []

# 类：大驼峰
class NewsCrawler:
    pass

# 常量：全大写
MAX_RETRY_COUNT = 3
```

**注释规范**:
```python
def analyze_sentiment(text: str) -> dict:
    """
    分析文本情感

    Args:
        text: 待分析的文本内容

    Returns:
        包含情感标签和置信度的字典
        {
            "label": "positive",
            "confidence": 0.92
        }
    """
    pass
```

### JavaScript/React 规范

```bash
# 代码格式化
npx prettier --write "src/**/*.{js,jsx}"

# 代码检查
npx eslint src/
```

**组件规范**:
```jsx
// 函数组件优先
function HotNews({ newsList, onNewsClick }) {
  // Hooks 放在最前面
  const [selectedNews, setSelectedNews] = useState(null);

  // 事件处理函数
  const handleNewsClick = useCallback((news) => {
    setSelectedNews(news);
    onNewsClick?.(news);
  }, [onNewsClick]);

  // 渲染
  return (
    <div className="hot-news">
      {newsList.map((news) => (
        <NewsItem
          key={news.id}
          news={news}
          onClick={handleNewsClick}
        />
      ))}
    </div>
  );
}

export default HotNews;
```

---

## 🧪 测试

### 后端测试

```bash
# 运行所有测试
pytest backend/tests/ -v

# 运行单个测试
pytest backend/tests/test_user_module.py::test_register_user -v

# 查看测试覆盖率
pytest backend/tests/ --cov=backend --cov-report=html
```

**测试示例**:
```python
# backend/tests/test_user_module.py
import pytest
from backend.user_module import register_user

def test_register_guest():
    """测试游客注册"""
    result = register_user({
        "username": "Guest",
        "phone": "",
        "keywords": ""
    })
    assert result["success"] is True
    assert "unique_id" in result["data"]

def test_register_with_phone():
    """测试手机号注册"""
    # 先发送验证码
    # 再验证验证码
    # 最后注册
    pass
```

### 前端测试

```bash
# 单元测试
npm test

# E2E 测试
npm run test:e2e

# 单文件测试
npm test -- src/components/HotNews.test.js
```

**测试示例**:
```jsx
// src/components/HotNews.test.js
import { render, screen, fireEvent } from '@testing-library/react';
import HotNews from './HotNews';

test('渲染新闻列表', () => {
  const mockNews = [
    { id: 1, title: '新闻 1' },
    { id: 2, title: '新闻 2' }
  ];

  render(<HotNews newsList={mockNews} />);

  expect(screen.getByText('新闻 1')).toBeInTheDocument();
  expect(screen.getByText('新闻 2')).toBeInTheDocument();
});

test('点击新闻触发回调', () => {
  const handleClick = jest.fn();
  const mockNews = [{ id: 1, title: '新闻 1' }];

  render(<HotNews newsList={mockNews} onNewsClick={handleClick} />);

  fireEvent.click(screen.getByText('新闻 1'));

  expect(handleClick).toHaveBeenCalledWith(mockNews[0]);
});
```

---

## 🐛 调试技巧

### 后端调试

**使用 Python debugger**:
```python
import pdb

def analyze_news(text):
    pdb.set_trace()  # 设置断点
    result = some_analysis(text)
    return result
```

**Flask 调试模式**:
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
flask run
```

**日志调试**:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fetch_news():
    logger.debug("开始抓取新闻")
    # ...
    logger.info(f"抓取到 {len(news_list)} 条新闻")
```

### 前端调试

**React Developer Tools**:
安装 Chrome 扩展：React Developer Tools

**Console 调试**:
```javascript
// 使用 console 方法
console.log('状态变化:', keywords);
console.warn('这个函数即将废弃');
console.error('发生错误:', error);

// 使用 debugger 语句
function handleLogin() {
  debugger;  // 浏览器会在此暂停
  // ...
}
```

**网络请求调试**:
```javascript
// 在浏览器 DevTools 中查看 Network 标签
// 或者使用 fetch 拦截器
fetch('/api/news/hot')
  .then(response => response.json())
  .then(data => console.log('API 响应:', data))
  .catch(error => console.error('API 错误:', error));
```

---

## 📦 模块开发指南

### 添加新的数据源

**Step 1**: 在 `config/config.yaml` 添加配置
```yaml
platforms:
  - id: "new_platform"
    name: "新平台"
```

**Step 2**: 在 `config/rss_mapping.yaml` 添加 RSS 地址（如有）
```yaml
rss_mapping:
  new_platform:
    url: "https://example.com/feed"
    region: domestic
```

**Step 3**: 创建爬虫文件 `crawlers/new_platform.py`
```python
from crawlers.base import BaseCrawler, NewsItem

class NewPlatformCrawler(BaseCrawler):
    platform = "new_platform"
    platform_name = "新平台"

    async def fetch(self) -> list[NewsItem]:
        # 实现抓取逻辑
        news_items = []
        # ...
        return news_items
```

**Step 4**: 在 `crawlers/__init__.py` 注册
```python
from .new_platform import NewPlatformCrawler

__all__ = ['NewPlatformCrawler', ...]
```

---

### 添加新的 API 接口

**Step 1**: 创建或编辑蓝图文件
```python
# backend/news_module.py
from flask import Blueprint

news_bp = Blueprint('news', __name__)

@news_bp.route('/api/news/custom', methods=['GET'])
def custom_news():
    """自定义新闻接口"""
    from flask import request
    limit = request.args.get('limit', 20)

    # 业务逻辑
    news_list = fetch_custom_news(limit)

    return jsonify({
        "success": True,
        "data": {"news": news_list}
    })
```

**Step 2**: 在主应用中注册蓝图
```python
# backend/app.py
from flask import Flask
from .news_module import news_bp

app = Flask(__name__)
app.register_blueprint(news_bp)
```

---

### 添加新的前端组件

**Step 1**: 创建组件文件
```jsx
// src/components/CustomComponent.jsx
import React from 'react';

function CustomComponent({ data, onUpdate }) {
  return (
    <div className="custom-component">
      {/* 组件内容 */}
    </div>
  );
}

export default CustomComponent;
```

**Step 2**: 在 App.jsx 中导入使用
```jsx
import CustomComponent from './components/CustomComponent';

function App() {
  return (
    <div>
      <CustomComponent data={...} onUpdate={...} />
    </div>
  );
}
```

---

## 🔧 开发工具

### 后端工具

**HTTP 客户端**:
- Postman: API 测试
- curl: 命令行测试
- httpie: 更友好的 curl 替代

```bash
# 使用 httpie 测试 API
http GET localhost:5100/api/news/hot limit==10
```

**数据库工具**:
- DB Browser for SQLite: SQLite 可视化
- Neo4j Browser: Neo4j 查询

```bash
# SQLite 命令行
sqlite3 database.sqlite3

# 查看表
.tables

# 查询数据
SELECT * FROM Users LIMIT 10;
```

### 前端工具

**开发服务器**:
```bash
cd frontend-new
npm run dev  # Vite 开发服务器
```

**构建工具**:
```bash
# 生产构建
npm run build

# 预览构建结果
npm run preview
```

**代码质量**:
```bash
# 格式化代码
npx prettier --write "src/**/*.{js,jsx}"

# ESLint 检查
npx eslint src/ --fix
```

---

## 🚀 部署

### 开发环境部署
```bash
./deploy.sh  # 一键部署脚本
```

### 生产环境部署

**Docker 部署**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**手动部署**:
```bash
# 1. 安装依赖
pip install -r backend/requirements.txt
cd frontend-new && npm install

# 2. 构建前端
cd frontend-new
npm run build

# 3. 配置 Nginx
# 将 frontend-new/dist 目录配置到 Nginx

# 4. 启动后端
cd backend
gunicorn -w 4 -b 0.0.0.0:5100 app:app
```

---

## 📚 资源链接

### 官方文档
- [Flask 文档](https://flask.palletsprojects.com/)
- [React 文档](https://react.dev/)
- [Neo4j 文档](https://neo4j.com/docs/)

### 内部文档
- [README.md](README.md) - 项目介绍
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构设计
- [QUICKSTART.md](QUICKSTART.md) - 快速开始
- [API.md](API.md) - API 文档

---

## 🤝 贡献流程

1. **Fork 项目**
2. **创建分支**: `git checkout -b feature/your-feature`
3. **开发功能**: 编写代码和测试
4. **提交代码**: `git commit -m "feat: add new feature"`
5. **推送分支**: `git push origin feature/your-feature`
6. **创建 PR**: 在 GitHub 上提交 Pull Request

**Commit 规范**:
```
feat: 新功能
fix: bug 修复
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

---

## 📞 联系方式

- **GitHub Issues**: https://github.com/njndxjj/lumos/issues
- **开发群**: (内部群)

---

*最后更新：2026-03-15*
