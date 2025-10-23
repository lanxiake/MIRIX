#!/bin/bash

# 更新后端服务脚本
# 用途: 拉取最新代码和镜像，重启后端服务
# 作者: Claude Code
# 日期: 2025-10-23

set -e  # 遇到错误立即退出

# 默认使用 docker-compose.yml，可通过参数指定其他配置文件
COMPOSE_FILE="${1:-docker-compose.yml}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 打印分隔线
print_separator() {
    echo -e "${BLUE}================================================================${NC}"
}

# 检查是否在正确的目录
check_directory() {
    log_info "检查当前目录..."
    log_info "使用配置文件: ${COMPOSE_FILE}"

    if [ ! -f "${COMPOSE_FILE}" ]; then
        log_error "未找到 ${COMPOSE_FILE} 文件"
        log_error "请确保在 /opt/MIRIX 目录下运行此脚本"
        log_error "用法: ./scripts/update_backend_service.sh [docker-compose文件]"
        log_error "示例: ./scripts/update_backend_service.sh docker-compose.test.yml"
        exit 1
    fi
    log_success "目录检查通过: $(pwd)"
    log_success "配置文件检查通过: ${COMPOSE_FILE}"
}

# 拉取最新代码
pull_latest_code() {
    print_separator
    log_info "步骤 1/5: 拉取最新代码..."

    # 检查当前分支
    CURRENT_BRANCH=$(git branch --show-current)
    log_info "当前分支: $CURRENT_BRANCH"

    # 检查是否有未提交的更改
    if ! git diff-index --quiet HEAD --; then
        log_warning "检测到未提交的更改:"
        git status --short
        log_warning "将保留这些更改并尝试拉取..."
    fi

    # 拉取最新代码
    log_info "执行 git pull origin $CURRENT_BRANCH..."
    if git pull origin "$CURRENT_BRANCH"; then
        log_success "代码更新成功"

        # 显示最新的提交
        log_info "最新提交信息:"
        git log -1 --oneline --decorate
    else
        log_error "代码拉取失败"
        exit 1
    fi
}

# 拉取最新镜像
pull_latest_image() {
    print_separator
    log_info "步骤 2/5: 拉取最新后端镜像..."

    IMAGE_NAME="10.157.152.192:10443/mirix/backend"
    TARGET_VERSION="v1.0.8"

    log_info "拉取镜像: ${IMAGE_NAME}:${TARGET_VERSION}"
    if docker pull "${IMAGE_NAME}:${TARGET_VERSION}"; then
        log_success "镜像拉取成功: ${IMAGE_NAME}:${TARGET_VERSION}"

        # 同时更新 latest 标签
        log_info "拉取镜像: ${IMAGE_NAME}:latest"
        docker pull "${IMAGE_NAME}:latest" || log_warning "latest 标签拉取失败（可忽略）"
    else
        log_error "镜像拉取失败"
        exit 1
    fi

    # 显示镜像信息
    log_info "镜像详细信息:"
    docker images "${IMAGE_NAME}" | head -3
}

# 停止并移除旧容器
stop_old_container() {
    print_separator
    log_info "步骤 3/5: 停止并移除旧的后端容器..."

    # 检查容器是否存在
    if docker-compose -f "${COMPOSE_FILE}" ps mirix-backend | grep -q "mirix-backend"; then
        log_info "停止后端容器..."
        docker-compose -f "${COMPOSE_FILE}" stop mirix-backend

        log_info "移除后端容器..."
        docker-compose -f "${COMPOSE_FILE}" rm -f mirix-backend
        log_success "旧容器已停止并移除"
    else
        log_warning "未找到运行中的后端容器"
    fi
}

# 启动新容器
start_new_container() {
    print_separator
    log_info "步骤 4/5: 启动新的后端容器..."

    log_info "执行 docker-compose -f ${COMPOSE_FILE} up -d mirix-backend..."
    if docker-compose -f "${COMPOSE_FILE}" up -d mirix-backend; then
        log_success "后端容器启动成功"
    else
        log_error "后端容器启动失败"
        exit 1
    fi

    # 等待容器启动
    log_info "等待容器完全启动 (15秒)..."
    sleep 15

    # 检查容器状态
    log_info "检查容器状态..."
    docker-compose -f "${COMPOSE_FILE}" ps mirix-backend
}

# 验证服务健康状态
verify_service() {
    print_separator
    log_info "步骤 5/5: 验证服务健康状态..."

    # 检查容器日志
    log_info "最近的容器日志 (最后20行):"
    echo "----------------------------------------"
    docker-compose -f "${COMPOSE_FILE}" logs mirix-backend --tail 20
    echo "----------------------------------------"

    # 检查健康状态
    log_info "检查 /health 端点..."
    sleep 5  # 再等待5秒确保服务完全启动

    if curl -s http://localhost:47283/health > /dev/null; then
        log_success "健康检查通过! 后端服务正常运行"

        # 显示健康检查结果
        log_info "健康检查响应:"
        curl -s http://localhost:47283/health | jq . || curl -s http://localhost:47283/health
    else
        log_warning "健康检查失败，但这可能是正常的（服务可能仍在初始化）"
        log_info "请手动检查日志: docker-compose -f ${COMPOSE_FILE} logs -f mirix-backend"
    fi
}

# 打印总结
print_summary() {
    print_separator
    log_success "后端服务更新完成!"
    echo ""
    log_info "配置信息:"
    echo "  - 配置文件: ${COMPOSE_FILE}"
    echo "  - 后端地址: http://10.157.152.40:47283"
    echo "  - 镜像版本: v1.0.9"
    echo "  - 修复内容: 在 send_message 方法中添加详细日志，追踪请求处理流程"
    echo ""
    log_info "后续操作:"
    echo "  1. 从前端发送测试消息: \"我的名字叫做toolan\""
    echo "  2. 观察后端日志: docker-compose -f ${COMPOSE_FILE} logs -f mirix-backend"
    echo "  3. 验证核心记忆是否成功保存"
    echo ""
    log_info "如果遇到问题，请查看完整日志:"
    echo "  docker-compose -f ${COMPOSE_FILE} logs mirix-backend --tail 100"
    print_separator
}

# 主函数
main() {
    echo ""
    print_separator
    log_info "开始更新 MIRIX 后端服务..."
    log_info "脚本版本: 1.1.0"
    log_info "配置文件: ${COMPOSE_FILE}"
    log_info "执行时间: $(date '+%Y-%m-%d %H:%M:%S')"
    print_separator
    echo ""

    # 执行各个步骤
    check_directory
    pull_latest_code
    pull_latest_image
    stop_old_container
    start_new_container
    verify_service

    echo ""
    print_summary
}

# 捕获错误
trap 'log_error "脚本执行失败! 错误发生在第 $LINENO 行"' ERR

# 运行主函数
main "$@"
