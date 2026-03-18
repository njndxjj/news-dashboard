#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目配置文件
从环境变量读取配置，支持服务器部署
"""

import os

# 项目根目录（自动检测）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 服务端口配置
BACKEND_PORT = int(os.environ.get('BACKEND_PORT', 5000))
FRONTEND_PORT = int(os.environ.get('FRONTEND_PORT', 3000))
PROXY_PORT = int(os.environ.get('PROXY_PORT', 8080))

# 服务地址配置
BACKEND_HOST = os.environ.get('BACKEND_HOST', 'localhost')
FRONTEND_HOST = os.environ.get('FRONTEND_HOST', 'localhost')

# 服务 URL
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
FRONTEND_URL = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"

# 定时任务配置
REFRESH_INTERVAL = int(os.environ.get('REFRESH_INTERVAL', 600))  # 秒，默认 10 分钟
API_URL = f"{BACKEND_URL}/api/refresh"

# 目录配置
LUMOS_DIR = os.path.join(BASE_DIR, 'Lumos')
FRONTEND_DIR = os.path.join(LUMOS_DIR, 'frontend-new')

# PID 文件目录（使用系统临时目录）
PID_DIR = os.environ.get('PID_DIR', '/tmp')
LOG_DIR = os.environ.get('LOG_DIR', '/tmp')

# PID 文件路径
BACKEND_PID_FILE = os.path.join(PID_DIR, 'newsnow_backend.pid')
FRONTEND_PID_FILE = os.path.join(PID_DIR, 'newsnow_frontend.pid')
PROXY_PID_FILE = os.path.join(PID_DIR, 'newsnow_proxy.pid')
REFRESH_PID_FILE = os.path.join(PID_DIR, 'newsnow_refresh.pid')

# 日志文件路径
BACKEND_LOG = os.path.join(LOG_DIR, 'backend.log')
FRONTEND_LOG = os.path.join(LOG_DIR, 'frontend.log')
PROXY_LOG = os.path.join(LOG_DIR, 'proxy.log')
REFRESH_LOG = os.path.join(LOG_DIR, 'refresh.log')
