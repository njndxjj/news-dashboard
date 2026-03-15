# 基于 Python 的后端 Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制必要文件
COPY backend/ /app/

# 安装依赖
RUN pip install --no-cache-dir flask && pip install qwen-sdk

# 启动后端服务
CMD [ "python", "app.py", "--port=5100" ]