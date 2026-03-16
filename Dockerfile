FROM python:3.11-slim

WORKDIR /app

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 完全禁用 apt 签名验证（解决网络环境问题）
RUN echo "APT::Get::AllowUnauthenticated 'true';" > /etc/apt/apt.conf.d/99allow-unauthenticated && \
    echo "Acquire::AllowInsecureRepositories 'true';" >> /etc/apt/apt.conf.d/99allow-unauthenticated && \
    echo "Acquire::AllowDowngradeToInsecureRepositories 'true';" >> /etc/apt/apt.conf.d/99allow-unauthenticated

# 安装系统依赖（包括 cron 和 supervisor）
RUN apt-get -o Acquire::AllowInsecureRepositories=true update && \
    apt-get install -y --no-install-recommends \
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
    cron \
    supervisor \
    curl && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.org/simple && \
    playwright install chromium

# 复制应用代码
COPY monitor_app.py .
COPY database.py .
COPY feishu_push.py .
COPY run_crawlers.py .
COPY crawlers/ crawlers/
COPY templates/ templates/
COPY config/ config/

# 创建 static 目录（可能为空）
RUN mkdir -p /app/static
# 复制 Lumos 模块（包含 user_module 等）
COPY Lumos/ Lumos/

# 复制 supervisor 配置文件
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 复制 cron 配置文件
COPY cronjob /etc/cron.d/news-cron
RUN chmod 0644 /etc/cron.d/news-cron

# 创建数据目录和日志目录
RUN mkdir -p /app/data /var/log/supervisor

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/news || exit 1

# 使用 supervisord 同时管理 cron 和 Flask
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
