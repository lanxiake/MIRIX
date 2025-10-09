#!/bin/bash
# MCP Server Docker容器运行脚本
#
# 功能：
# 1. 启动/停止/重启MCP Server容器
# 2. 查看容器状态和日志
# 3. 容器健康检查
#
# 使用方法：
#   bash scripts/docker/run_mcp.sh [命令] [选项]
#
# 命令：
#   start    启动容器
#   stop     停止容器
#   restart  重启容器
#   status   查看容器状态
#   logs     查看容器日志
#   shell    进入容器shell
#   clean    清理容器和镜像

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
CONTAINER_NAME="mcp-server"
IMAGE_NAME="mirix-mcp-server:latest"
HOST_PORT="18002"
CONTAINER_PORT="18002"
NETWORK="bridge"
ENV_FILE=""
DETACH=true
RESTART_POLICY="unless-stopped"

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# 显示帮助信息
show_help() {
    cat << EOF
MCP Server Docker容器管理脚本

使用方法:
    $0 [命令] [选项]

命令:
    start     启动容器
    stop      停止容器
    restart   重启容器
    status    查看容器状态
    logs      查看容器日志
    shell     进入容器shell
    clean     清理容器和镜像
    health    检查容器健康状态

选项:
    --name NAME       容器名称 (默认: mcp-server)
    --image IMAGE     镜像名称 (默认: mirix-mcp-server:latest)
    --port PORT       主机端口 (默认: 18002)
    --env-file FILE   环境变量文件
    --network NET     Docker网络 (默认: bridge)
    --no-detach       前台运行容器
    --help            显示此帮助信息

示例:
    $0 start                              # 启动容器
    $0 start --port 8080                  # 指定端口启动
    $0 start --env-file .env.prod         # 使用环境文件启动
    $0 logs -f                           # 实时查看日志
    $0 shell                             # 进入容器shell
    $0 clean                             # 清理所有相关资源

环境变量:
    MCP_CONTAINER_NAME   容器名称
    MCP_IMAGE_NAME       镜像名称
    MCP_HOST_PORT        主机端口
EOF
}

# 检查Docker是否可用
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装或不可用"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker 服务未运行"
        exit 1
    fi
}

# 检查容器是否存在
container_exists() {
    docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"
}

# 检查容器是否运行
container_running() {
    docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"
}

# 启动容器
start_container() {
    print_info "启动 MCP Server 容器..."
    
    # 检查容器是否已存在
    if container_exists; then
        if container_running; then
            print_warning "容器 $CONTAINER_NAME 已在运行"
            return 0
        else
            print_info "启动现有容器 $CONTAINER_NAME"
            docker start "$CONTAINER_NAME"
            print_success "容器启动成功"
            return 0
        fi
    fi
    
    # 构建docker run命令
    RUN_CMD="docker run"
    
    if [ "$DETACH" = true ]; then
        RUN_CMD="$RUN_CMD -d"
    fi
    
    RUN_CMD="$RUN_CMD --name $CONTAINER_NAME"
    RUN_CMD="$RUN_CMD --restart $RESTART_POLICY"
    RUN_CMD="$RUN_CMD -p $HOST_PORT:$CONTAINER_PORT"
    RUN_CMD="$RUN_CMD --network $NETWORK"
    
    # 添加环境变量文件
    if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
        RUN_CMD="$RUN_CMD --env-file $ENV_FILE"
    fi
    
    # 添加默认环境变量
    RUN_CMD="$RUN_CMD -e MCP_SSE_HOST=0.0.0.0"
    RUN_CMD="$RUN_CMD -e MCP_SSE_PORT=$CONTAINER_PORT"
    
    RUN_CMD="$RUN_CMD $IMAGE_NAME"
    
    print_info "执行命令: $RUN_CMD"
    eval "$RUN_CMD"
    
    print_success "容器创建并启动成功"
    print_info "容器名称: $CONTAINER_NAME"
    print_info "访问地址: http://localhost:$HOST_PORT/sse"
}

# 停止容器
stop_container() {
    print_info "停止 MCP Server 容器..."
    
    if ! container_exists; then
        print_warning "容器 $CONTAINER_NAME 不存在"
        return 0
    fi
    
    if ! container_running; then
        print_warning "容器 $CONTAINER_NAME 未运行"
        return 0
    fi
    
    docker stop "$CONTAINER_NAME"
    print_success "容器停止成功"
}

# 重启容器
restart_container() {
    print_info "重启 MCP Server 容器..."
    stop_container
    sleep 2
    start_container
}

# 查看容器状态
show_status() {
    print_info "MCP Server 容器状态:"
    
    if container_exists; then
        docker ps -a --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"
        
        if container_running; then
            echo ""
            print_info "容器资源使用情况:"
            docker stats "$CONTAINER_NAME" --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
        fi
    else
        print_warning "容器 $CONTAINER_NAME 不存在"
    fi
}

# 查看容器日志
show_logs() {
    if ! container_exists; then
        print_error "容器 $CONTAINER_NAME 不存在"
        exit 1
    fi
    
    print_info "查看 MCP Server 容器日志:"
    docker logs "$@" "$CONTAINER_NAME"
}

# 进入容器shell
enter_shell() {
    if ! container_running; then
        print_error "容器 $CONTAINER_NAME 未运行"
        exit 1
    fi
    
    print_info "进入 MCP Server 容器 shell:"
    docker exec -it "$CONTAINER_NAME" /bin/bash
}

# 检查容器健康状态
check_health() {
    if ! container_running; then
        print_error "容器 $CONTAINER_NAME 未运行"
        exit 1
    fi
    
    print_info "检查 MCP Server 健康状态:"
    
    # 检查容器健康状态
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")
    print_info "容器健康状态: $HEALTH_STATUS"
    
    # 检查端口连通性
    if command -v curl &> /dev/null; then
        if curl -s "http://localhost:$HOST_PORT/health" &> /dev/null; then
            print_success "服务端点可访问"
        else
            print_warning "服务端点不可访问"
        fi
    fi
    
    # 显示最近的日志
    print_info "最近的日志:"
    docker logs --tail 10 "$CONTAINER_NAME"
}

# 清理容器和镜像
clean_resources() {
    print_warning "这将删除容器和相关镜像，确定要继续吗? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_info "操作已取消"
        return 0
    fi
    
    print_info "清理 MCP Server 相关资源..."
    
    # 停止并删除容器
    if container_exists; then
        if container_running; then
            docker stop "$CONTAINER_NAME"
        fi
        docker rm "$CONTAINER_NAME"
        print_success "容器已删除"
    fi
    
    # 删除镜像
    if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "$IMAGE_NAME"; then
        docker rmi "$IMAGE_NAME"
        print_success "镜像已删除"
    fi
    
    # 清理未使用的资源
    docker system prune -f
    print_success "清理完成"
}

# 解析命令行参数
COMMAND=""
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        start|stop|restart|status|logs|shell|health|clean)
            COMMAND="$1"
            shift
            ;;
        --name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        --image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --port)
            HOST_PORT="$2"
            shift 2
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --network)
            NETWORK="$2"
            shift 2
            ;;
        --no-detach)
            DETACH=false
            shift
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

# 使用环境变量覆盖默认值
CONTAINER_NAME="${MCP_CONTAINER_NAME:-$CONTAINER_NAME}"
IMAGE_NAME="${MCP_IMAGE_NAME:-$IMAGE_NAME}"
HOST_PORT="${MCP_HOST_PORT:-$HOST_PORT}"

# 检查Docker
check_docker

# 如果没有指定命令，显示帮助
if [ -z "$COMMAND" ]; then
    show_help
    exit 1
fi

# 执行相应命令
case $COMMAND in
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${EXTRA_ARGS[@]}"
        ;;
    shell)
        enter_shell
        ;;
    health)
        check_health
        ;;
    clean)
        clean_resources
        ;;
    *)
        print_error "未知命令: $COMMAND"
        show_help
        exit 1
        ;;
esac
