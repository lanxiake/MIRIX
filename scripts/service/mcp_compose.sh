#!/bin/bash
# MCP Server Docker Compose 管理脚本
#
# 功能：
# 1. 使用Docker Compose管理MCP Server服务栈
# 2. 支持开发和生产环境配置
# 3. 服务健康检查和日志管理
#
# 使用方法：
#   bash scripts/service/mcp_compose.sh [命令] [选项]

set -e

# 颜色输出函数
print_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# 默认配置
COMPOSE_FILE="mcp_server/docker-compose.yml"
ENV_FILE="mcp_server/.env"
PROJECT_NAME="mirix-mcp"

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# 显示帮助信息
show_help() {
    cat << EOF
MCP Server Docker Compose 管理脚本

使用方法:
    $0 [命令] [选项]

命令:
    up        启动服务栈
    down      停止服务栈
    restart   重启服务栈
    status    查看服务状态
    logs      查看服务日志
    build     构建镜像
    pull      拉取镜像
    ps        查看容器状态
    exec      在容器中执行命令

选项:
    --env-file FILE    环境变量文件 (默认: mcp_server/.env)
    --compose-file FILE Docker Compose文件 (默认: mcp_server/docker-compose.yml)
    --project-name NAME 项目名称 (默认: mirix-mcp)
    --build            启动时重新构建镜像
    --detach           后台运行
    --help             显示此帮助信息

示例:
    $0 up                                 # 启动服务栈
    $0 up --build                         # 重新构建并启动
    $0 logs -f mcp-server                 # 实时查看MCP服务日志
    $0 exec mcp-server bash               # 进入MCP容器
    $0 down                               # 停止服务栈
EOF
}

# 检查Docker Compose
check_docker_compose() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装或不可用"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null && ! docker-compose --version &> /dev/null; then
        print_error "Docker Compose 未安装或不可用"
        exit 1
    fi
    
    # 优先使用 docker compose (新版本)
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
}

# 构建compose命令
build_compose_cmd() {
    local cmd="$COMPOSE_CMD"
    
    if [ -n "$COMPOSE_FILE" ]; then
        cmd="$cmd -f $COMPOSE_FILE"
    fi
    
    if [ -n "$PROJECT_NAME" ]; then
        cmd="$cmd -p $PROJECT_NAME"
    fi
    
    if [ -f "$ENV_FILE" ]; then
        cmd="$cmd --env-file $ENV_FILE"
    fi
    
    echo "$cmd"
}

# 启动服务栈
start_services() {
    print_info "启动 MCP Server 服务栈..."
    
    local compose_cmd=$(build_compose_cmd)
    local up_args="up"
    
    # 解析额外参数
    for arg in "$@"; do
        case $arg in
            --build)
                up_args="$up_args --build"
                ;;
            --detach|-d)
                up_args="$up_args -d"
                ;;
            *)
                up_args="$up_args $arg"
                ;;
        esac
    done
    
    cd "$PROJECT_ROOT"
    
    print_info "执行命令: $compose_cmd $up_args"
    $compose_cmd $up_args
    
    print_success "服务栈启动完成"
    
    # 显示服务状态
    sleep 3
    show_status
}

# 停止服务栈
stop_services() {
    print_info "停止 MCP Server 服务栈..."
    
    local compose_cmd=$(build_compose_cmd)
    cd "$PROJECT_ROOT"
    
    $compose_cmd down "$@"
    
    print_success "服务栈已停止"
}

# 重启服务栈
restart_services() {
    print_info "重启 MCP Server 服务栈..."
    stop_services
    sleep 2
    start_services "$@"
}

# 查看服务状态
show_status() {
    print_info "MCP Server 服务栈状态:"
    
    local compose_cmd=$(build_compose_cmd)
    cd "$PROJECT_ROOT"
    
    $compose_cmd ps
    
    echo ""
    print_info "服务健康状态:"
    
    # 检查MCP Server健康状态
    if command -v curl &> /dev/null; then
        if curl -s --max-time 5 "http://localhost:18002/health" &> /dev/null; then
            print_success "MCP Server 服务可访问"
        else
            print_warning "MCP Server 服务不可访问"
        fi
    fi
}

# 查看服务日志
show_logs() {
    local compose_cmd=$(build_compose_cmd)
    cd "$PROJECT_ROOT"
    
    print_info "查看服务日志:"
    $compose_cmd logs "$@"
}

# 构建镜像
build_images() {
    print_info "构建 MCP Server 镜像..."
    
    local compose_cmd=$(build_compose_cmd)
    cd "$PROJECT_ROOT"
    
    $compose_cmd build "$@"
    
    print_success "镜像构建完成"
}

# 拉取镜像
pull_images() {
    print_info "拉取镜像..."
    
    local compose_cmd=$(build_compose_cmd)
    cd "$PROJECT_ROOT"
    
    $compose_cmd pull "$@"
    
    print_success "镜像拉取完成"
}

# 查看容器状态
show_containers() {
    local compose_cmd=$(build_compose_cmd)
    cd "$PROJECT_ROOT"
    
    $compose_cmd ps "$@"
}

# 在容器中执行命令
exec_command() {
    local compose_cmd=$(build_compose_cmd)
    cd "$PROJECT_ROOT"
    
    $compose_cmd exec "$@"
}

# 解析命令行参数
COMMAND=""
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        up|down|restart|status|logs|build|pull|ps|exec)
            COMMAND="$1"
            shift
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --compose-file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        --project-name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            EXTRA_ARGS+=("$1")
            shift
            ;;
    esac
done

# 检查Docker Compose
check_docker_compose

# 如果没有指定命令，显示帮助
if [ -z "$COMMAND" ]; then
    show_help
    exit 1
fi

# 执行相应命令
case $COMMAND in
    up)
        start_services "${EXTRA_ARGS[@]}"
        ;;
    down)
        stop_services "${EXTRA_ARGS[@]}"
        ;;
    restart)
        restart_services "${EXTRA_ARGS[@]}"
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${EXTRA_ARGS[@]}"
        ;;
    build)
        build_images "${EXTRA_ARGS[@]}"
        ;;
    pull)
        pull_images "${EXTRA_ARGS[@]}"
        ;;
    ps)
        show_containers "${EXTRA_ARGS[@]}"
        ;;
    exec)
        exec_command "${EXTRA_ARGS[@]}"
        ;;
    *)
        print_error "未知命令: $COMMAND"
        show_help
        exit 1
        ;;
esac
