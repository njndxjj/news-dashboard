#!/bin/bash

# 资讯监控系统 - 一键更新脚本
# 支持平滑升级、自动备份和回滚

set -e

echo "========================================="
echo "  资讯监控系统 - 一键更新脚本"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 备份目录
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 函数：打印信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函数：检查 Docker 是否运行
check_docker() {
    if ! docker-compose ps &> /dev/null; then
        print_error "容器未运行，请先执行部署：sudo ./deploy.sh"
        exit 1
    fi
}

# 函数：备份数据
backup_data() {
    print_info "正在备份数据..."

    # 创建备份目录
    mkdir -p "$BACKUP_DIR"

    # 备份数据库
    if [ -f "./data/data.db" ]; then
        docker exec news-monitor-app cp /app/data/data.db ./data/data.db.backup
        cp ./data/data.db "$BACKUP_DIR/data.db.${TIMESTAMP}.bak"
        print_success "数据库已备份：$BACKUP_DIR/data.db.${TIMESTAMP}.bak"
    fi

    # 备份当前代码版本
    git rev-parse HEAD > "$BACKUP_DIR/version.${TIMESTAMP}.txt" 2>/dev/null || echo "unknown" > "$BACKUP_DIR/version.${TIMESTAMP}.txt"

    print_success "版本信息已保存：$BACKUP_DIR/version.${TIMESTAMP}.txt"
}

# 函数：回滚
rollback() {
    print_warning "开始回滚到上一个版本..."

    # 找到最新的备份
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/data.db.*.bak 2>/dev/null | head -1)

    if [ -z "$LATEST_BACKUP" ]; then
        print_error "未找到备份文件，无法回滚"
        exit 1
    fi

    print_info "使用备份：$LATEST_BACKUP"

    # 停止容器
    docker-compose down

    # 恢复数据库
    cp "$LATEST_BACKUP" ./data/data.db

    # 启动容器
    docker-compose up -d

    print_success "回滚完成！"
    print_info "如需查看备份列表：ls -lh $BACKUP_DIR"
}

# 函数：清理旧备份（保留最近 7 个）
cleanup_old_backups() {
    print_info "清理旧备份（保留最近 7 个）..."

    cd "$BACKUP_DIR"
    ls -t data.db.*.bak 2>/dev/null | tail -n +8 | xargs -r rm
    ls -t version.*.txt 2>/dev/null | tail -n +8 | xargs -r rm
    cd ..

    print_success "旧备份已清理"
}

# 主流程
echo ""
echo "请选择操作："
echo "  1) 更新到最新版本 (pull & rebuild)"
echo "  2) 回滚到上一个版本"
echo "  3) 查看备份列表"
echo "  4) 退出"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        print_info "开始更新流程..."
        echo ""

        # 1. 检查环境
        print_info "检查 Docker 环境..."
        if ! command -v docker &> /dev/null; then
            print_error "未安装 Docker"
            exit 1
        fi

        if ! command -v git &> /dev/null; then
            print_error "未安装 Git"
            exit 1
        fi

        # 2. 备份当前版本
        backup_data
        echo ""

        # 3. 拉取最新代码
        print_info "拉取最新代码..."
        git fetch origin

        CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
        print_info "当前分支：$CURRENT_BRANCH"

        git pull origin "$CURRENT_BRANCH"
        print_success "代码已更新"
        echo ""

        # 4. 检查 .env 文件
        if [ -f ".env.example" ] && [ ! -f ".env" ]; then
            print_warning ".env 文件不存在，从 .env.example 复制..."
            cp .env.example .env
            print_error "请编辑 .env 文件，填入 DASHSCOPE_API_KEY"
            read -p "按回车键继续..."
        fi
        echo ""

        # 5. 重新构建并启动
        print_info "重新构建 Docker 镜像（这可能需要几分钟）..."
        docker-compose build --no-cache

        print_info "停止旧容器..."
        docker-compose down

        print_info "启动新容器..."
        docker-compose up -d

        # 6. 等待服务启动
        print_info "等待服务启动..."
        sleep 15

        # 7. 健康检查
        print_info "执行健康检查..."
        if docker-compose ps | grep -q "Up"; then
            print_success "✓ 容器运行正常"

            # 测试 API
            sleep 5
            if curl -s http://localhost:5000/api/news > /dev/null 2>&1; then
                print_success "✓ API 响应正常"
            else
                print_warning "API 暂时未响应，可能需要更长时间启动"
            fi
        else
            print_error "容器启动失败！"
            echo ""
            print_info "查看日志：docker-compose logs"
            print_info "回滚命令：./update.sh (选择选项 2)"
            exit 1
        fi

        # 8. 清理旧备份
        cleanup_old_backups

        echo ""
        print_success "========================================="
        print_success "  更新完成！"
        print_success "========================================="
        echo ""
        print_info "查看日志：docker-compose logs -f"
        print_info "访问服务：http://localhost:5000"
        echo ""

        # 显示更新日志
        if [ -f "CHANGELOG.md" ]; then
            print_info "最近更新："
            head -30 CHANGELOG.md
        fi
        ;;

    2)
        rollback
        ;;

    3)
        print_info "备份列表："
        echo ""
        ls -lh "$BACKUP_DIR" 2>/dev/null || print_warning "暂无备份"
        echo ""
        ;;

    4)
        print_info "已退出"
        exit 0
        ;;

    *)
        print_error "无效选项"
        exit 1
        ;;
esac
