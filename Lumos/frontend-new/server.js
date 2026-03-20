import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import httpProxy from 'http-proxy';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;
const HOST = process.env.HOST || '0.0.0.0'; // 服务器环境监听所有接口

// Production configuration for server deployment
// BACKEND_URL can be configured via environment variable
// In production with Nginx, /api requests will be proxied to backend service
// Use the server IP or domain name where backend is running
const BACKEND_URL = process.env.BACKEND_URL || 'http://47.238.241.204:5000'; // Change to server IP
console.log(`[Configuration] Backend URL configured as: ${BACKEND_URL}`);

// Configure http-proxy for API requests
const apiProxy = httpProxy.createProxyServer({
  target: BACKEND_URL,
  changeOrigin: true,
  // 添加错误处理选项
  proxyTimeout: 120000, // 2分钟超时
  timeout: 120000,      // 2分钟超时
});

// Handle proxy errors
apiProxy.on('error', (err, req, res) => {
  console.error('[Proxy Error]', err);
  if (res.writeHead) {
    res.writeHead(502, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: '后端服务暂时不可用，请稍后重试' }));
  }
});

// Middleware to parse JSON and handle CORS for production
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Enable CORS for all routes (necessary in some server environments)
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization, X-User-ID');
  if (req.method === 'OPTIONS') {
    res.sendStatus(200);
  } else {
    next();
  }
});

// API proxy middleware - intercept /api requests and forward to backend
app.use('/api', (req, res, next) => {
  console.log(`[Proxy] ${req.method} ${req.originalUrl}`);
  apiProxy.web(req, res, {
    target: BACKEND_URL,
  });
});

// Static file serving from dist directory with cache control for production
app.use(express.static(path.join(__dirname, 'dist'), {
  maxAge: '1d', // 缓存1天
  etag: true,   // 启用ETag
}));

// Admin routes
app.get('/admin/behavior', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'behavior.html'));
});

app.get('/admin/interest-graph', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'interest-graph.html'));
});

app.get('/admin', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'admin.html'));
});

// Fallback route - serve index.html for all other routes (SPA)
app.get(/^(?!\/api).*$/, (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

const server = app.listen(PORT, HOST, () => {
  console.log(`🚀 Lumos 前端服务器运行在 http://${HOST}:${PORT}`);
  console.log(`📊 后端 API 地址：${BACKEND_URL}`);
  console.log(`📁 静态文件目录：${path.join(__dirname, 'dist')}`);
  console.log(`🔐 监听地址：${HOST}`);
  console.log('');
  console.log('✅ 服务器启动成功！');
  console.log('💡 提示：在生产环境中建议使用 Nginx 作为反向代理');
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    console.log('Process terminated');
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  server.close(() => {
    console.log('Process terminated');
  });
});
