FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（包括浏览器依赖）
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    libgbm1 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# 设置 Playwright 浏览器路径
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码
COPY monitor_app.py .
COPY database.py .
COPY feishu_push.py .
COPY templates/ templates/
COPY static/ static/

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/news || exit 1

# 运行应用
CMD ["python", "monitor_app.py"]
