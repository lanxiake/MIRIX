#!/bin/bash
# MIRIX Docker 部署脚本
# 版本: 1.0
# 使用方法: ./deploy.sh [选项]

set -e  # 出错时退出

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
    cat << EOF
MIRIX Docker 部署脚本

使用方法:
    ./deploy.sh [选项]

选项:
    -h, --help          显示此帮助信息
    -e, --env           仅设置环境变量
    -b, --build         强制重新构建镜像
    -d, --dev           使用开发环境配置
    -s, --stop          停止所有服务
    -c, --clean         清理所有数据和镜像
    -l, --logs          查看服务日志
    -p, --check         检查部署状态
    --tools             启动开发工具 (仅开发模式)

示例:
    ./deploy.sh                    # 标准部署
    ./deploy.sh -d                 # 开发环境部署
    ./deploy.sh -d --tools         # 开发环境 + 工具
    ./deploy.sh -b                 # 重新构建并部署
    ./deploy.sh -s                 # 停止服务
    ./deploy.sh -c                 # 清理所有数据

EOF
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."

    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装！请先安装 Docker。"
        exit 1
    fi

    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装！请先安装 Docker Compose。"
        exit 1
    fi

    # 检查 Docker 版本
    DOCKER_VERSION=$(docker --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
    if [[ $(echo "$DOCKER_VERSION < 20.10" | bc -l) -eq 1 ]]; then
        log_warning "Docker 版本较低 ($DOCKER_VERSION)，推荐使用 20.10+"
    fi

    # 检查内存
    MEMORY_GB=$(free -g | awk 'NR==2{print $2}')
    if [[ $MEMORY_GB -lt 4 ]]; then
        log_warning "系统内存不足 (${MEMORY_GB}GB)，推荐至少 4GB"
    fi

    log_success "系统要求检查完成"
}

# 设置环境变量
setup_environment() {
    log_info "设置环境变量..."

    if [[ ! -f .env ]]; then
        if [[ -f .env.example ]]; then
            cp .env.example .env
            log_info "已创建 .env 文件，请编辑配置 API 密钥"
            echo
            log_warning "请编辑 .env 文件，至少配置一个 LLM API 密钥:"
            echo "  - OPENAI_API_KEY"
            echo "  - ANTHROPIC_API_KEY"
            echo "  - GOOGLE_AI_API_KEY"
            echo "  - DEEPSEEK_API_KEY"
            echo
            read -p "是否现在编辑 .env 文件？ (y/n): " edit_env
            if [[ $edit_env == "y" || $edit_env == "Y" ]]; then
                ${EDITOR:-nano} .env
            else
                log_warning "请手动编辑 .env 文件后重新运行脚本"
                exit 1
            fi
        else
            log_error ".env.example 文件不存在！"
            exit 1
        fi
    else
        log_info ".env 文件已存在"
    fi

    # 验证必需的环境变量
    source .env
    API_KEY_COUNT=0
    [[ -n "$OPENAI_API_KEY" && "$OPENAI_API_KEY" != "your_openai_api_key_here" ]] && ((API_KEY_COUNT++))
    [[ -n "$ANTHROPIC_API_KEY" && "$ANTHROPIC_API_KEY" != "your_anthropic_api_key_here" ]] && ((API_KEY_COUNT++))
    [[ -n "$GOOGLE_AI_API_KEY" && "$GOOGLE_AI_API_KEY" != "your_google_ai_api_key_here" ]] && ((API_KEY_COUNT++))
    [[ -n "$DEEPSEEK_API_KEY" && "$DEEPSEEK_API_KEY" != "your_deepseek_api_key_here" ]] && ((API_KEY_COUNT++))

    if [[ $API_KEY_COUNT -eq 0 ]]; then
        log_error "未配置任何有效的 LLM API 密钥！"
        exit 1
    fi

    log_success "环境变量配置完成 (已配置 $API_KEY_COUNT 个 API 密钥)"
}

# 检查端口占用
check_ports() {
    log_info "检查端口占用..."

    PORTS=(5432 6380 47283 18001 18002)
    for port in "${PORTS[@]}"; do
        if ss -tulpn | grep -q ":$port "; then
            log_warning "端口 $port 已被占用"
            ss -tulpn | grep ":$port "
        fi
    done
}

# 构建镜像
build_images() {
    log_info "构建 Docker 镜像..."

    if [[ $FORCE_BUILD == true ]]; then
        docker-compose build --no-cache --pull
    else
        docker-compose build
    fi

    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."

    if [[ $DEV_MODE == true ]]; then
        COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
        if [[ $WITH_TOOLS == true ]]; then
            COMPOSE_FILES="$COMPOSE_FILES --profile tools"
        fi
        docker-compose $COMPOSE_FILES up -d
    else
        docker-compose up -d
    fi

    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."

    # 等待数据库
    log_info "等待 PostgreSQL..."
    timeout 60 bash -c 'until docker-compose exec -T postgres pg_isready -U mirix; do sleep 2; done'

    # 等待 Redis
    log_info "等待 Redis..."
    timeout 30 bash -c 'until docker-compose exec -T redis redis-cli ping | grep -q PONG; do sleep 2; done'

    # 等待后端服务
    log_info "等待后端服务..."
    timeout 120 bash -c 'until curl -sf http://localhost:47283/health > /dev/null 2>&1; do sleep 5; done'

    # 等待前端服务
    log_info "等待前端服务..."
    timeout 60 bash -c 'until curl -sf http://localhost:18001/health > /dev/null 2>&1; do sleep 5; done'

    # 等待 MCP 服务
    log_info "等待 MCP 服务..."
    timeout 60 bash -c 'until curl -sf http://localhost:18002/sse > /dev/null 2>&1; do sleep 5; done'

    log_success "所有服务就绪"
}

# 检查部署状态
check_deployment() {
    log_info "检查部署状态..."

    echo
    echo "=== 服务状态 ==="
    docker-compose ps

    echo
    echo "=== 健康检查 ==="

    # 后端健康检查
    if curl -sf http://localhost:47283/health > /dev/null 2>&1; then
        log_success "后端服务: OK"
    else
        log_error "后端服务: 失败"
    fi

    # 前端健康检查
    if curl -sf http://localhost:18001/health > /dev/null 2>&1; then
        log_success "前端服务: OK"
    else
        log_error "前端服务: 失败"
    fi

    # MCP 健康检查
    if curl -sf http://localhost:18002/sse > /dev/null 2>&1; then
        log_success "MCP 服务: OK"
    else
        log_error "MCP 服务: 失败"
    fi

    echo
    echo "=== 访问地址 ==="
    echo "前端应用:    http://localhost:18001"
    echo "API 文档:    http://localhost:47283/docs"
    echo "MCP SSE:     http://localhost:18002/sse"

    if [[ $DEV_MODE == true && $WITH_TOOLS == true ]]; then
        echo
        echo "=== 开发工具 ==="
        echo "pgAdmin:     http://localhost:5050"
        echo "Redis 管理:  http://localhost:8081"
        echo "邮件测试:    http://localhost:8025"
    fi
}

# 显示日志
show_logs() {
    log_info "显示服务日志..."
    docker-compose logs --tail=100 -f
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose down
    log_success "服务已停止"
}

# 清理数据
clean_all() {
    read -p "这将删除所有数据和镜像，确认继续？ (yes/no): " confirm
    if [[ $confirm != "yes" ]]; then
        log_info "操作已取消"
        exit 0
    fi

    log_info "清理所有数据..."
    docker-compose down -v --rmi all
    docker system prune -f
    log_success "清理完成"
}

# 主函数
main() {
    # 解析命令行参数
    FORCE_BUILD=false
    DEV_MODE=false
    WITH_TOOLS=false
    ENV_ONLY=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -e|--env)
                ENV_ONLY=true
                shift
                ;;
            -b|--build)
                FORCE_BUILD=true
                shift
                ;;
            -d|--dev)
                DEV_MODE=true
                shift
                ;;
            -s|--stop)
                stop_services
                exit 0
                ;;
            -c|--clean)
                clean_all
                exit 0
                ;;
            -l|--logs)
                show_logs
                exit 0
                ;;
            -p|--check)
                check_deployment
                exit 0
                ;;
            --tools)
                WITH_TOOLS=true
                shift
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 显示标题
    echo "========================================"
    echo "       MIRIX Docker 部署脚本"
    echo "========================================"
    echo

    # 检查系统要求
    check_requirements

    # 设置环境变量
    setup_environment

    if [[ $ENV_ONLY == true ]]; then
        log_success "环境变量设置完成"
        exit 0
    fi

    # 检查端口占用
    check_ports

    # 构建镜像
    build_images

    # 启动服务
    start_services

    # 等待服务就绪
    wait_for_services

    # 检查部署状态
    check_deployment

    echo
    log_success "MIRIX 部署完成！"

    if [[ $DEV_MODE == true ]]; then
        echo
        log_info "开发模式已启用，支持代码热重载"
        log_info "使用 './deploy.sh -l' 查看日志"
        log_info "使用 './deploy.sh -s' 停止服务"
    fi
}

# 运行主函数
main "$@"