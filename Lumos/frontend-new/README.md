# Lumos 前端应用

基于 React 18 + Vite 构建的现代化舆情监控平台前端应用。

---

## ✨ 特性

- 🚀 **高性能** - Vite 构建，HMR 热更新
- 📱 **响应式** - 适配桌面和移动端
- 🎨 **现代化 UI** - 优雅的界面设计
- 🔐 **用户系统** - 完整的登录/注册流程
- 📊 **数据可视化** - 知识图谱、行为仪表板
- 🤖 **AI 集成** - 智能分析和推荐
- 🌐 **国际化** - 支持多语言 (计划中)

---

## 📁 目录结构

```
frontend-new/
├── public/                     # 静态资源
│   ├── favicon.svg
│   ├── index.html
│   └── icons.svg
├── src/
│   ├── App.jsx                 # 主应用组件
│   ├── App.css                 # 应用样式
│   ├── main.jsx                # 入口文件
│   ├── index.css               # 全局样式
│   ├── components/             # UI 组件
│   │   ├── HotNews.js          # 热门新闻
│   │   ├── AIAnalysis.js       # AI 分析
│   │   ├── Recommendation.js   # 个性化推荐
│   │   ├── KnowledgeGraph.jsx  # 知识图谱
│   │   ├── UserInterests.js    # 兴趣管理
│   │   ├── UserBehaviorDashboard.jsx  # 用户行为
│   │   ├── PushManagement.js   # 推送管理
│   │   ├── Toast.jsx           # 通知组件
│   │   └── Toast.css
│   ├── services/
│   │   ├── api.js              # API 服务封装
│   │   └── api.jsx             # API 请求方法
│   ├── hooks/
│   │   └── useToast.js         # Toast Hook
│   ├── utils/
│   │   └── tracking.js         # 埋点追踪
│   └── assets/                 # 资源文件
│       ├── react.svg
│       ├── vite.svg
│       └── hero.png
├── package.json                # 依赖配置
├── vite.config.js              # Vite 配置
├── eslint.config.js            # ESLint 配置
└── README.md                   # 本文档
```

---

## 🚀 快速启动

### 1. 安装依赖
```bash
cd frontend-new
npm install
```

### 2. 启动开发服务器
```bash
npm run dev
```

访问 `http://localhost:5173`

### 3. 生产构建
```bash
npm run build
```

### 4. 预览构建结果
```bash
npm run preview
```

---

## 🧩 核心组件

### App.jsx
应用根组件，管理全局状态和路由。

**主要功能**:
- 用户登录状态管理
- 兴趣标签管理
- AI 分析和推荐新闻获取
- 页面浏览埋点

**状态示例**:
```jsx
const [isLoggedIn, setIsLoggedIn] = useState(false);
const [uniqueId, setUniqueId] = useState(null);
const [keywords, setKeywords] = useState([]);
const [news, setNews] = useState([]);
const [insights, setInsights] = useState(null);
```

### HotNews.js
展示热门新闻列表，支持实时刷新。

**特性**:
- 按热度排序
- 来源标识
- 发布时间
- 点击跳转

### AIAnalysis.js
显示 AI 分析结果，包括情感、关键词、摘要。

**分析维度**:
- 情感分析 (正面/中性/负面)
- 关键词提取
- 智能摘要
- 实体识别

### Recommendation.js
个性化推荐新闻，基于用户兴趣和行为。

**推荐算法**:
- 内容推荐 (标签匹配)
- 协同过滤 (用户相似度)
- 热门榜单

### KnowledgeGraph.jsx
知识图谱可视化，展示实体关系。

**可视化**:
- 力导向图
- 节点交互
- 关系筛选
- 详情面板

### UserInterests.js
用户兴趣标签管理。

**预设分类**:
- 科技领域
- 宏观政策
- 行业趋势
- 经营管理
- 市场营销
- 财税金融
- 法律合规
- 技术升级
- 供应链

### UserBehaviorDashboard.jsx
用户行为数据仪表板。

**统计维度**:
- 浏览次数
- 点击次数
- 偏好分类
- 活跃时段

### Toast.jsx
全局通知组件。

**通知类型**:
- success (成功)
- error (错误)
- info (信息)
- warning (警告)

---

## 🔌 API 集成

### api.js
封装所有 API 请求。

**使用方法**:
```javascript
import { apiRequest } from './services/api.js';

// GET 请求
const news = await apiRequest('get', '/api/news/hot');

// POST 请求
const user = await apiRequest('post', '/api/users/register', {
  username: 'Guest',
  phone: '',
  keywords: ''
});
```

### 错误处理
```javascript
try {
  const data = await apiRequest('get', '/api/news/hot');
} catch (error) {
  console.error('API 请求失败:', error);
  error('获取新闻失败，请稍后重试');
}
```

---

## 📊 埋点追踪

### tracking.js
用户行为埋点。

**追踪事件**:
```javascript
// 页面浏览
trackPageView('home', {
  unique_id: uniqueId,
  is_logged_in: isLoggedIn
});

// 新闻点击
trackNewsClick(newsId, position);

// 兴趣更新
trackInterestUpdate(keywords);
```

---

## 🎨 样式规范

### CSS 命名
```css
/* 使用 BEM 命名 */
.hot-news { }
.hot-news__item { }
.hot-news__item--active { }

/* 使用 Tailwind CSS */
<div className="flex items-center space-x-4">
  <h1 className="text-2xl font-bold text-gray-900">
    热门新闻
  </h1>
</div>
```

### 响应式设计
```css
@media (max-width: 768px) {
  .news-grid {
    grid-template-columns: 1fr;
  }
}
```

---

## 🧪 测试

### 单元测试
```bash
npm test
```

### 测试示例
```jsx
import { render, screen } from '@testing-library/react';
import HotNews from './HotNews';

test('渲染新闻列表', () => {
  const mockNews = [
    { id: 1, title: '新闻 1' },
    { id: 2, title: '新闻 2' }
  ];

  render(<HotNews newsList={mockNews} />);

  expect(screen.getByText('新闻 1')).toBeInTheDocument();
});
```

---

## 🔧 配置

### vite.config.js
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:5100'
    }
  }
})
```

### .eslintrc
```json
{
  "extends": ["react-app", "prettier"],
  "rules": {
    "react/prop-types": "off"
  }
}
```

---

## 📦 依赖

### 核心依赖
```json
{
  "react": "^18.x",
  "react-dom": "^18.x",
  "axios": "^1.x"
}
```

### 开发依赖
```json
{
  "vite": "^5.x",
  "@vitejs/plugin-react": "^4.x",
  "eslint": "^8.x",
  "prettier": "^3.x"
}
```

---

## 🐛 常见问题

### Q: 开发服务器启动失败
A: 检查 Node.js 版本是否 >= 16，端口 5173 是否被占用

### Q: API 请求跨域
A: 检查 vite.config.js 中的 proxy 配置

### Q: 构建失败
A: 删除 `node_modules` 和 `package-lock.json`，重新 `npm install`

---

## 🚀 性能优化

### 代码分割
```javascript
// 懒加载组件
const KnowledgeGraph = lazy(() => import('./components/KnowledgeGraph'));
```

### 图片优化
```jsx
// 使用 WebP 格式
<img src="hero.webp" alt="Hero" loading="lazy" />
```

### 虚拟滚动
```jsx
// 长列表使用虚拟滚动
<VirtualList
  data={newsList}
  itemHeight={80}
  renderItem={(item) => <NewsItem key={item.id} news={item} />}
/>
```

---

## 📚 资源

- [React 文档](https://react.dev/)
- [Vite 文档](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

---

*最后更新：2026-03-15*
