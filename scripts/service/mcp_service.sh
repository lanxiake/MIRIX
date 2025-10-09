#!/bin/bash
# MCP Server 服务管理脚本
#
# 功能：
# 1. 启动/停止/重启MCP Server服务
# 2. 查看服务状态和日志
# 3. 支持开发模式和生产模式
# 4. 服务健康检查和自动恢复
#
# 使用方法：
#   bash scripts/service/mcp_service.sh [命令] [选项]
#
# 命令：
#   start     启动服务
#   stop      停止服务
#   restart   重启服务
#   status    查看服务状态
#   logs      查看服务日志
#   health    健康检查
#   install   安装为系统服务
#   uninstall 卸载系统服务

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
SERVICE_NAME="mcp-server"
MODE="production"  # development 或 production
PID_FILE="/var/run/mcp-server.pid"
LOG_FILE="/var/log/mcp-server.log"
CONFIG_FILE=""
DAEMON_MODE=true
AUTO_RESTART=true

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv_mcp"

# 显示帮助信息
show_help() {
    cat << EOF
MCP Server 服务管理脚本

使用方法:
    $0 [命令] [选项]

命令:
    start      启动服务
    stop       停止服务
    restart    重启服务
    status     查看服务状态
    logs       查看服务日志
    health     健康检查
    install    安装为系统服务
    uninstall  卸载系统服务

选项:
    --mode MODE        运行模式 (development/production, 默认: production)
    --config FILE      配置文件路径
    --pid-file FILE    PID文件路径 (默认: /var/run/mcp-server.pid)
    --log-file FILE    日志文件路径 (默认: /var/log/mcp-server.log)
    --no-daemon        前台运行，不作为守护进程
    --no-auto-restart  禁用自动重启
    --help             显示此帮助信息

示例:
    $0 start                              # 启动生产模式服务
    $0 start --mode development           # 启动开发模式服务
    $0 start --config /path/to/config     # 使用指定配置启动
    $0 logs -f                           # 实时查看日志
    $0 status                            # 查看服务状态
    $0 install                           # 安装为系统服务

环境变量:
    MCP_SERVICE_MODE     服务运行模式
    MCP_CONFIG_FILE      配置文件路径
    MCP_PID_FILE         PID文件路径
    MCP_LOG_FILE         日志文件路径
EOF
}

# 检查权限
check_permissions() {
    if [ "$MODE" = "production" ]; then
        # 生产模式需要root权限
        if [ "$EUID" -ne 0 ]; then
            print_error "生产模式需要root权限，请使用 sudo 运行"
            exit 1
        fi
    else
        # 开发模式使用用户权限
        PID_FILE="/tmp/mcp-server-dev.pid"
        LOG_FILE="/tmp/mcp-server-dev.log"
    fi
}

# 检查依赖
check_dependencies() {
    # 检查Python虚拟环境
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Python虚拟环境不存在: $VENV_DIR"
        print_info "请先运行: bash scripts/dev/setup_mcp_dev.sh"
        exit 1
    fi
    
    # 检查MCP Server模块
    if [ ! -f "$PROJECT_ROOT/mcp_server/main.py" ]; then
        print_error "MCP Server模块不存在"
        exit 1
    fi
}

# 获取服务PID
get_service_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

# 检查服务是否运行
is_service_running() {
    local pid=$(get_service_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# 启动服务
start_service() {
    print_info "启动 MCP Server 服务 ($MODE 模式)..."
    
    if is_service_running; then
        print_warning "服务已在运行 (PID: $(get_service_pid))"
        return 0
    fi
    
    # 清理旧的PID文件
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
    fi
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 切换到项目根目录
    cd "$PROJECT_ROOT"
    
    # 构建启动命令
    START_CMD="python -m mcp_server"
    
    if [ "$MODE" = "development" ]; then
        START_CMD="$START_CMD --debug --log-level DEBUG"
    fi
    
    if [ -n "$CONFIG_FILE" ]; then
        START_CMD="$START_CMD --config $CONFIG_FILE"
    fi
    
    # 启动服务
    if [ "$DAEMON_MODE" = true ]; then
        # 守护进程模式
        nohup $START_CMD > "$LOG_FILE" 2>&1 &
        local pid=$!
        echo $pid > "$PID_FILE"
        
        # 等待服务启动
        sleep 3
        
        if is_service_running; then
            print_success "服务启动成功 (PID: $pid)"
            print_info "日志文件: $LOG_FILE"
            print_info "PID文件: $PID_FILE"
        else
            print_error "服务启动失败，请查看日志: $LOG_FILE"
            exit 1
        fi
    else
        # 前台模式
        print_info "前台运行模式，按 Ctrl+C 停止服务"
        exec $START_CMD
    fi
}

# 停止服务
stop_service() {
    print_info "停止 MCP Server 服务..."
    
    if ! is_service_running; then
        print_warning "服务未运行"
        return 0
    fi
    
    local pid=$(get_service_pid)
    print_info "正在停止服务 (PID: $pid)..."
    
    # 发送TERM信号
    kill -TERM "$pid" 2>/dev/null || true
    
    # 等待服务停止
    local count=0
    while [ $count -lt 10 ] && kill -0 "$pid" 2>/dev/null; do
        sleep 1
        count=$((count + 1))
    done
    
    # 如果还未停止，强制杀死
    if kill -0 "$pid" 2>/dev/null; then
        print_warning "服务未响应TERM信号，强制停止..."
        kill -KILL "$pid" 2>/dev/null || true
    fi
    
    # 清理PID文件
    rm -f "$PID_FILE"
    
    print_success "服务已停止"
}

# 重启服务
restart_service() {
    print_info "重启 MCP Server 服务..."
    stop_service
    sleep 2
    start_service
}

# 查看服务状态
show_status() {
    print_info "MCP Server 服务状态:"
    
    if is_service_running; then
        local pid=$(get_service_pid)
        print_success "服务正在运行 (PID: $pid)"
        
        # 显示进程信息
        if command -v ps &> /dev/null; then
            echo ""
            print_info "进程信息:"
            ps -p "$pid" -o pid,ppid,user,cpu,mem,etime,cmd --no-headers || true
        fi
        
        # 显示端口监听情况
        if command -v netstat &> /dev/null; then
            echo ""
            print_info "端口监听:"
            netstat -tlnp 2>/dev/null | grep ":18002" || print_warning "未找到18002端口监听"
        fi
    else
        print_error "服务未运行"
        
        # 检查是否有残留的PID文件
        if [ -f "$PID_FILE" ]; then
            print_warning "发现残留的PID文件: $PID_FILE"
        fi
    fi
    
    # 显示最近的日志
    if [ -f "$LOG_FILE" ]; then
        echo ""
        print_info "最近的日志 (最后10行):"
        tail -n 10 "$LOG_FILE"
    fi
}

# 查看服务日志
show_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        print_error "日志文件不存在: $LOG_FILE"
        exit 1
    fi
    
    print_info "查看 MCP Server 服务日志:"
    tail "$@" "$LOG_FILE"
}

# 健康检查
health_check() {
    print_info "MCP Server 健康检查:"
    
    if ! is_service_running; then
        print_error "服务未运行"
        return 1
    fi
    
    local pid=$(get_service_pid)
    print_success "服务进程正常 (PID: $pid)"
    
    # 检查端口连通性
    if command -v curl &> /dev/null; then
        if curl -s --max-time 5 "http://localhost:18002/health" &> /dev/null; then
            print_success "服务端点可访问"
        else
            print_warning "服务端点不可访问"
            return 1
        fi
    elif command -v wget &> /dev/null; then
        if wget -q --timeout=5 --tries=1 "http://localhost:18002/health" -O /dev/null; then
            print_success "服务端点可访问"
        else
            print_warning "服务端点不可访问"
            return 1
        fi
    else
        print_warning "无法检查端点连通性 (缺少curl或wget)"
    fi
    
    print_success "健康检查通过"
    return 0
}

# 安装为系统服务
install_systemd_service() {
    if [ "$EUID" -ne 0 ]; then
        print_error "安装系统服务需要root权限"
        exit 1
    fi
    
    print_info "安装 MCP Server 为系统服务..."
    
    # 创建systemd服务文件
    local service_file="/etc/systemd/system/mcp-server.service"
    cat > "$service_file" << EOF
[Unit]
Description=MIRIX MCP Server
After=network.target
Wants=network.target

[Service]
Type=forking
User=mirix
Group=mirix
WorkingDirectory=$PROJECT_ROOT
Environment=PATH=$VENV_DIR/bin
ExecStart=$PROJECT_ROOT/scripts/service/mcp_service.sh start --mode production --no-daemon
ExecStop=$PROJECT_ROOT/scripts/service/mcp_service.sh stop
ExecReload=$PROJECT_ROOT/scripts/service/mcp_service.sh restart
PIDFile=$PID_FILE
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd配置
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable mcp-server
    
    print_success "系统服务安装完成"
    print_info "使用以下命令管理服务:"
    echo "  systemctl start mcp-server    # 启动服务"
    echo "  systemctl stop mcp-server     # 停止服务"
    echo "  systemctl restart mcp-server  # 重启服务"
    echo "  systemctl status mcp-server   # 查看状态"
    echo "  systemctl enable mcp-server   # 开机自启"
    echo "  systemctl disable mcp-server  # 禁用自启"
}

# 卸载系统服务
uninstall_systemd_service() {
    if [ "$EUID" -ne 0 ]; then
        print_error "卸载系统服务需要root权限"
        exit 1
    fi
    
    print_info "卸载 MCP Server 系统服务..."
    
    # 停止并禁用服务
    systemctl stop mcp-server 2>/dev/null || true
    systemctl disable mcp-server 2>/dev/null || true
    
    # 删除服务文件
    local service_file="/etc/systemd/system/mcp-server.service"
    if [ -f "$service_file" ]; then
        rm -f "$service_file"
    fi
    
    # 重新加载systemd配置
    systemctl daemon-reload
    
    print_success "系统服务卸载完成"
}

# 解析命令行参数
COMMAND=""
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        start|stop|restart|status|logs|health|install|uninstall)
            COMMAND="$1"
            shift
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --pid-file)
            PID_FILE="$2"
            shift 2
            ;;
        --log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        --no-daemon)
            DAEMON_MODE=false
            shift
            ;;
        --no-auto-restart)
            AUTO_RESTART=false
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
MODE="${MCP_SERVICE_MODE:-$MODE}"
CONFIG_FILE="${MCP_CONFIG_FILE:-$CONFIG_FILE}"
PID_FILE="${MCP_PID_FILE:-$PID_FILE}"
LOG_FILE="${MCP_LOG_FILE:-$LOG_FILE}"

# 检查权限和依赖
check_permissions
check_dependencies

# 如果没有指定命令，显示帮助
if [ -z "$COMMAND" ]; then
    show_help
    exit 1
fi

# 执行相应命令
case $COMMAND in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${EXTRA_ARGS[@]}"
        ;;
    health)
        health_check
        ;;
    install)
        install_systemd_service
        ;;
    uninstall)
        uninstall_systemd_service
        ;;
    *)
        print_error "未知命令: $COMMAND"
        show_help
        exit 1
        ;;
esac
