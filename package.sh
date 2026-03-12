#!/bin/bash

# 资讯监控系统 - 打包脚本
# 用于准备生产环境部署包

set -e

echo "========================================="
echo "  资讯监控系统 - 打包脚本"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 版本号（可通过参数传入）
VERSION=${1:-"latest"}

# 包名
PACKAGE_NAME="news-monitor-${VERSION}"

# 创建临时目录
TEMP_DIR="/tmp/${PACKAGE_NAME}"
rm -rf "${TEMP_DIR}"
mkdir -p "${TEMP_DIR}"

echo -e "${YELLOW}正在准备打包文件...${NC}"

# 复制必要文件
cp -r monitor_app.py "${TEMP_DIR}/"
cp -r database.py "${TEMP_DIR}/"
cp -r feishu_push.py "${TEMP_DIR}/"
cp -r templates "${TEMP_DIR}/"
cp -r static "${TEMP_DIR}/"
cp -r config "${TEMP_DIR}/"
cp -r crawlers "${TEMP_DIR}/"
cp -r data "${TEMP_DIR}/"

# 复制配置文件
cp requirements.txt "${TEMP_DIR}/"
cp Dockerfile "${TEMP_DIR}/"
cp docker-compose.yml "${TEMP_DIR}/"
cp .env.example "${TEMP_DIR}/"
cp .dockerignore "${TEMP_DIR}/"
cp nginx.conf.example "${TEMP_DIR}/"
cp news-monitor.service "${TEMP_DIR}/"

# 复制文档
cp README.md "${TEMP_DIR}/"
cp DEPLOY.md "${TEMP_DIR}/"

# 创建数据目录占位符
mkdir -p "${TEMP_DIR}/data"
echo "# 数据目录 - 请确保此目录有写入权限" > "${TEMP_DIR}/data/README.md"

# 创建 .gitkeep 文件
touch "${TEMP_DIR}/data/.gitkeep"

# 创建版本文件
echo "Version: ${VERSION}" > "${TEMP_DIR}/VERSION"
echo "Build Date: $(date '+%Y-%m-%d %H:%M:%S')" >> "${TEMP_DIR}/VERSION"

# 创建快速启动脚本
cat > "${TEMP_DIR}/start.sh" << 'EOF'
#!/bin/bash
# 快速启动脚本

echo "检查环境..."

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "错误：未找到 .env 文件"
    echo "请执行：cp .env.example .env 并配置 API Key"
    exit 1
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误：未安装 Docker"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "启动服务..."
docker-compose up -d

echo ""
echo "服务已启动！"
echo "访问地址：http://localhost:5000"
echo "查看日志：docker-compose logs -f"
EOF

chmod +x "${TEMP_DIR}/start.sh"

# 打包
cd /tmp
echo ""
echo -e "${YELLOW}正在创建压缩包...${NC}"

# 创建 tar.gz 包
tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"

# 创建 zip 包
zip -rq "${PACKAGE_NAME}.zip" "${PACKAGE_NAME}"

# 清理临时目录
rm -rf "${TEMP_DIR}"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  打包完成！${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "生成的文件："
echo "  - /tmp/${PACKAGE_NAME}.tar.gz"
echo "  - /tmp/${PACKAGE_NAME}.zip"
echo ""
echo "文件大小："
ls -lh /tmp/${PACKAGE_NAME}.*
echo ""
echo "下一步："
echo "  1. 将压缩包上传到服务器"
echo "  2. 解压：tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "  3. 进入目录：cd ${PACKAGE_NAME}"
echo "  4. 配置环境：cp .env.example .env 并编辑"
echo "  5. 启动服务：./start.sh 或 docker-compose up -d"
echo ""
