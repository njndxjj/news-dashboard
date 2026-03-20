const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = 8080;
const HOST = '0.0.0.0';

// 代理API请求到后端（端口5000）
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:5000',
  changeOrigin: true,
  pathRewrite: {
    '^/api': '', // 移除/api前缀，直接转发到后端
  },
}));

// 代理其他请求到前端（端口3000）
app.use('/', createProxyMiddleware({
  target: 'http://localhost:3000',
  changeOrigin: true,
}));

app.listen(PORT, HOST, () => {
  console.log(`反向代理服务器运行在: http://${HOST}:${PORT}`);
  console.log(`所有请求将通过此代理统一处理，解决跨域问题`);
});