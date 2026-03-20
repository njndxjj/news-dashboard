module.exports = {
  apps: [
    {
      name: 'lumos-backend',
      script: './monitor_app.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        FLASK_ENV: 'production',
        // 服务器环境配置 - 监听所有网络接口
        HOST: '0.0.0.0',
        PORT: '5000'
      },
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    {
      name: 'lumos-scheduler',
      script: './scheduler.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        // 服务器环境配置
        PYTHONPATH: './'
      },
      error_file: './logs/scheduler-error.log',
      out_file: './logs/scheduler-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    {
      name: 'lumos-frontend',
      cwd: './Lumos/frontend-new',
      script: 'server.js',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      env: {
        NODE_ENV: 'production',
        PORT: '3000',
        // 服务器环境配置 - 指定后端服务地址
        BACKEND_URL: process.env.BACKEND_URL || 'http://47.238.241.204:5000',  // 使用实际服务器IP
        // 服务器环境下可能需要的其他配置
        HOST: '0.0.0.0'
      },
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    }
  ]
};