# 基于 Python 的后端 Dockerfile
FROM python:3.9-slim

# 安装 curl 用于健康检查
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY backend/requirements.txt /app/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器依赖
RUN playwright install chromium
RUN playwright install-deps chromium

# 复制后端代码
COPY backend/ /app/backend/
COPY *.py /app/
COPY crawlers/ /app/crawlers/
COPY config/ /app/config/
COPY templates/ /app/templates/

# 创建数据目录
RUN mkdir -p /app/logs /app/data

# 暴露端口
EXPOSE 5000

# 启动后端服务
ENV PORT=5000
ENV PYTHONUNBUFFERED=1
CMD ["python", "monitor_app.py"]