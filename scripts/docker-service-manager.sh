#!/bin/bash

# MIRIX Docker 服务管理脚本
# 用于构建、重启和管理Docker Compose服务

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "MIRIX Docker 服务管理脚本"
    echo ""
    echo "使用方法: $0 <服务名> [选项]"
    echo ""
    echo "可用服务:"
    echo "  mirix-backend     - 后端API服务"
    echo "  mirix-frontend    - 前端Web界面"
    echo "  mirix-mcp-sse     - MCP SSE服务"
    echo "  postgres          - PostgreSQL数据库"
    echo "  redis             - Redis缓存"
    echo "  all               - 所有服务"
    echo ""
    echo "选项:"
    echo "  --no-cache        - 构建时不使用缓存"
    echo "  --build-only      - 仅构建，不重启服务"
    echo "  --restart-only    - 仅重启，不重新构建"
    echo "  --logs            - 显示服务日志"
    echo "  --status          - 显示服务状态"
    echo "  -h, --help        - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 mirix-backend                  # 重新构建并重启后端服务"
    echo "  $0 mirix-frontend --no-cache      # 清理缓存重建前端"
    echo "  $0 mirix-backend --restart-only   # 仅重启后端服务"
    echo "  $0 mirix-backend --logs           # 查看后端日志"
    echo "  $0 all --status                   # 查看所有服务状态"
}

# 检查服务名是否有效
validate_service() {
    local service=$1
    local valid_services=("mirix-backend" "mirix-frontend" "mirix-mcp-sse" "postgres" "redis" "all")

    for valid in "${valid_services[@]}"; do
        if [[ "$valid" == "$service" ]]; then
            return 0
        fi
    done

    log_error "无效的服务名: $service"
    echo "可用服务: ${valid_services[*]}"
    return 1
}

# 构建服务
build_service() {
    local service=$1
    local no_cache=$2

    log_info "开始构建服务: $service"

    if [[ "$no_cache" == "true" ]]; then
        log_warning "使用 --no-cache 选项构建"
        if [[ "$service" == "all" ]]; then
            docker-compose build --no-cache
        else
            docker-compose build --no-cache "$service"
        fi
    else
        if [[ "$service" == "all" ]]; then
            docker-compose build
        else
            docker-compose build "$service"
        fi
    fi

    log_success "服务构建完成: $service"
}

# 停止服务
stop_service() {
    local service=$1

    log_info "停止服务: $service"

    if [[ "$service" == "all" ]]; then
        docker-compose down
    else
        docker-compose stop "$service"
    fi

    log_success "服务已停止: $service"
}

# 启动服务
start_service() {
    local service=$1

    log_info "启动服务: $service"

    if [[ "$service" == "all" ]]; then
        docker-compose up -d
    else
        docker-compose up -d "$service"
    fi

    log_success "服务已启动: $service"
}

# 重启服务
restart_service() {
    local service=$1

    log_info "重启服务: $service"

    if [[ "$service" == "all" ]]; then
        docker-compose restart
    else
        docker-compose restart "$service"
    fi

    log_success "服务已重启: $service"
}

# 显示服务日志
show_logs() {
    local service=$1

    log_info "显示服务日志: $service"

    if [[ "$service" == "all" ]]; then
        docker-compose logs -f --tail 50
    else
        docker-compose logs -f --tail 50 "$service"
    fi
}

# 显示服务状态
show_status() {
    local service=$1

    log_info "服务状态:"

    if [[ "$service" == "all" ]]; then
        docker-compose ps
    else
        docker-compose ps "$service"
    fi
}

# 完整的服务更新流程
update_service() {
    local service=$1
    local no_cache=$2

    log_info "开始完整更新流程: $service"

    # 1. 构建服务
    build_service "$service" "$no_cache"

    # 2. 停止服务
    if [[ "$service" == "all" ]]; then
        stop_service "$service"
    else
        docker-compose stop "$service"
    fi

    # 等待服务完全停止
    sleep 2

    # 3. 启动服务
    start_service "$service"

    # 等待服务启动
    sleep 5

    # 4. 显示状态
    show_status "$service"

    log_success "服务更新完成: $service"
}

# 主函数
main() {
    # 检查参数
    if [[ $# -eq 0 ]]; then
        log_error "请提供服务名"
        show_help
        exit 1
    fi

    local service=""
    local no_cache=false
    local build_only=false
    local restart_only=false
    local show_logs_flag=false
    local show_status_flag=false

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --no-cache)
                no_cache=true
                shift
                ;;
            --build-only)
                build_only=true
                shift
                ;;
            --restart-only)
                restart_only=true
                shift
                ;;
            --logs)
                show_logs_flag=true
                shift
                ;;
            --status)
                show_status_flag=true
                shift
                ;;
            *)
                if [[ -z "$service" ]]; then
                    service=$1
                else
                    log_error "未知参数: $1"
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # 验证服务名
    if ! validate_service "$service"; then
        exit 1
    fi

    # 切换到项目目录
    cd "$(dirname "$0")/.."

    log_info "当前目录: $(pwd)"
    log_info "目标服务: $service"

    # 执行相应操作
    if [[ "$show_logs_flag" == "true" ]]; then
        show_logs "$service"
    elif [[ "$show_status_flag" == "true" ]]; then
        show_status "$service"
    elif [[ "$build_only" == "true" ]]; then
        build_service "$service" "$no_cache"
    elif [[ "$restart_only" == "true" ]]; then
        restart_service "$service"
    else
        # 默认：完整更新流程
        update_service "$service" "$no_cache"
    fi
}

# 执行主函数
main "$@"