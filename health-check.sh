#!/bin/bash
# MIRIX 健康检查脚本
# 版本: 1.0
# 使用方法: ./health-check.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# 检查服务状态
check_service_status() {
    log_info "检查服务容器状态..."
    echo

    SERVICES=("mirix-postgres" "mirix-redis" "mirix-backend" "mirix-frontend" "mirix-mcp")

    for service in "${SERVICES[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$service"; then
            STATUS=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$service" | awk '{print $2}')
            if [[ $STATUS == "Up" ]]; then
                log_success "$service: $STATUS"
            else
                log_warning "$service: $STATUS"
            fi
        else
            log_error "$service: 未运行"
        fi
    done
}

# 检查端口连通性
check_port_connectivity() {
    log_info "检查端口连通性..."
    echo

    PORTS=(
        "5432:PostgreSQL"
        "6380:Redis"
        "47283:Backend API"
        "18001:Frontend"
        "18002:MCP Service"
    )

    for port_info in "${PORTS[@]}"; do
        PORT=$(echo $port_info | cut -d: -f1)
        SERVICE=$(echo $port_info | cut -d: -f2)

        if nc -z localhost $PORT 2>/dev/null; then
            log_success "$SERVICE (端口 $PORT): 可访问"
        else
            log_error "$SERVICE (端口 $PORT): 无法访问"
        fi
    done
}

# 检查健康端点
check_health_endpoints() {
    log_info "检查健康端点..."
    echo

    # 后端健康检查
    if curl -sf http://localhost:47283/health > /dev/null 2>&1; then
        RESPONSE=$(curl -s http://localhost:47283/health)
        log_success "后端健康检查: $RESPONSE"
    else
        log_error "后端健康检查: 失败"
    fi

    # 前端健康检查
    if curl -sf http://localhost:18001/health > /dev/null 2>&1; then
        log_success "前端健康检查: 正常"
    else
        log_error "前端健康检查: 失败"
    fi

    # MCP SSE 检查
    if curl -sf http://localhost:18002/sse > /dev/null 2>&1; then
        log_success "MCP SSE 连接: 正常"
    else
        log_error "MCP SSE 连接: 失败"
    fi
}

# 检查数据库连接
check_database_connection() {
    log_info "检查数据库连接..."
    echo

    # PostgreSQL 连接测试
    if docker-compose exec -T postgres pg_isready -U mirix > /dev/null 2>&1; then
        VERSION=$(docker-compose exec -T postgres psql -U mirix -d mirix -c "SELECT version();" -t | head -1 | xargs)
        log_success "PostgreSQL 连接: 正常"
        log_info "数据库版本: $VERSION"
    else
        log_error "PostgreSQL 连接: 失败"
    fi

    # Redis 连接测试
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis 连接: 正常"
        REDIS_INFO=$(docker-compose exec -T redis redis-cli info server | grep redis_version | cut -d: -f2 | tr -d '\r')
        log_info "Redis 版本: $REDIS_INFO"
    else
        log_error "Redis 连接: 失败"
    fi
}

# 检查资源使用情况
check_resource_usage() {
    log_info "检查资源使用情况..."
    echo

    # 容器资源使用
    echo "=== 容器资源使用 ==="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

    echo
    echo "=== 系统资源使用 ==="

    # 内存使用
    MEMORY_USAGE=$(free | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
    echo "内存使用: $MEMORY_USAGE"

    # 磁盘使用
    DISK_USAGE=$(df -h / | awk 'NR==2{print $5}')
    echo "磁盘使用: $DISK_USAGE"

    # 负载平均值
    LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}')
    echo "负载平均值:$LOAD_AVG"
}

# 检查日志错误
check_logs_for_errors() {
    log_info "检查服务日志错误..."
    echo

    SERVICES=("mirix-postgres" "mirix-redis" "mirix-backend" "mirix-frontend" "mirix-mcp")

    for service in "${SERVICES[@]}"; do
        ERROR_COUNT=$(docker logs "$service" --since="1h" 2>/dev/null | grep -i "error\|fail\|exception" | wc -l)
        if [[ $ERROR_COUNT -gt 0 ]]; then
            log_warning "$service: 发现 $ERROR_COUNT 个错误（最近1小时）"
        else
            log_success "$service: 无错误日志"
        fi
    done
}

# 检查配置
check_configuration() {
    log_info "检查配置..."
    echo

    # 检查环境变量
    if [[ -f .env ]]; then
        log_success ".env 文件: 存在"

        # 检查API密钥配置
        source .env
        API_KEY_COUNT=0
        [[ -n "$OPENAI_API_KEY" && "$OPENAI_API_KEY" != "your_openai_api_key_here" ]] && ((API_KEY_COUNT++))
        [[ -n "$ANTHROPIC_API_KEY" && "$ANTHROPIC_API_KEY" != "your_anthropic_api_key_here" ]] && ((API_KEY_COUNT++))
        [[ -n "$GOOGLE_AI_API_KEY" && "$GOOGLE_AI_API_KEY" != "your_google_ai_api_key_here" ]] && ((API_KEY_COUNT++))
        [[ -n "$DEEPSEEK_API_KEY" && "$DEEPSEEK_API_KEY" != "your_deepseek_api_key_here" ]] && ((API_KEY_COUNT++))

        if [[ $API_KEY_COUNT -gt 0 ]]; then
            log_success "API 密钥: 已配置 $API_KEY_COUNT 个"
        else
            log_error "API 密钥: 未配置"
        fi
    else
        log_error ".env 文件: 不存在"
    fi

    # 检查Docker Compose文件
    if [[ -f docker-compose.yml ]]; then
        log_success "docker-compose.yml: 存在"
    else
        log_error "docker-compose.yml: 不存在"
    fi
}

# 生成诊断报告
generate_diagnostic_report() {
    log_info "生成诊断报告..."

    REPORT_FILE="mirix_health_report_$(date +%Y%m%d_%H%M%S).txt"

    {
        echo "MIRIX 健康检查报告"
        echo "生成时间: $(date)"
        echo "========================"
        echo

        echo "=== 系统信息 ==="
        echo "操作系统: $(uname -a)"
        echo "Docker 版本: $(docker --version)"
        echo "Docker Compose 版本: $(docker-compose --version)"
        echo

        echo "=== 服务状态 ==="
        docker-compose ps
        echo

        echo "=== 容器日志 (最近10行) ==="
        for service in mirix-postgres mirix-redis mirix-backend mirix-frontend mirix-mcp; do
            echo "--- $service ---"
            docker logs "$service" --tail=10 2>/dev/null || echo "无法获取日志"
            echo
        done

        echo "=== 资源使用 ==="
        docker stats --no-stream
        echo
        free -h
        echo
        df -h
        echo

    } > "$REPORT_FILE"

    log_success "诊断报告已保存到: $REPORT_FILE"
}

# 主函数
main() {
    echo "========================================"
    echo "       MIRIX 健康检查"
    echo "========================================"
    echo

    # 检查Docker环境
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi

    # 执行检查
    check_service_status
    echo

    check_port_connectivity
    echo

    check_health_endpoints
    echo

    check_database_connection
    echo

    check_resource_usage
    echo

    check_logs_for_errors
    echo

    check_configuration
    echo

    # 生成报告
    if [[ "$1" == "--report" ]]; then
        generate_diagnostic_report
    fi

    echo "========================================"
    log_info "健康检查完成"
    echo
    log_info "使用 './health-check.sh --report' 生成详细诊断报告"
    echo "========================================"
}

# 运行主函数
main "$@"