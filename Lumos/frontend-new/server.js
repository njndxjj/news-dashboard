import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import httpProxy from 'http-proxy';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Docker 环境中使用服务名访问后端，本地开发使用 localhost
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:5000';
console.log(`[配置] 后端地址：${BACKEND_URL}`);

// 使用原生 http-proxy 创建代理服务器
const apiProxy = httpProxy.createProxyServer({
  target: BACKEND_URL,
  changeOrigin: true,
});

// 拦截 /api 请求并转发（保持完整路径）
app.use('/api', (req, res, next) => {
  console.log(`[代理] ${req.method} ${req.originalUrl}`);
  // 手动设置目标路径，保持 /api 前缀
  req.url = '/api' + req.url;  // 补回被 express 去掉的 /api
  console.log(`[代理重写] ${req.url}`);
  apiProxy.web(req, res, {
    target: BACKEND_URL,
  }, (err) => {
    console.error('[代理错误]', err);
    res.status(502).json({ error: '后端服务不可用' });
  });
});

// 静态文件服务（dist 目录）
app.use(express.static(path.join(__dirname, 'dist')));

// 用户行为分析路由 (必须在 /admin 之前)
app.get('/admin/behavior', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'behavior.html'));
});

// 兴趣图谱路由
app.get('/admin/interest-graph', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'interest-graph.html'));
});

// 管理后台路由
app.get('/admin', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'admin.html'));
});

// 默认路由
app.get('/*path', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Lumos 前端服务器运行在 http://localhost:${PORT}`);
  console.log(`后端 API 地址：${BACKEND_URL}`);
});
