#!/bin/bash
# MCP Server 开发环境设置脚本
# 
# 功能：
# 1. 创建Python虚拟环境
# 2. 安装项目依赖
# 3. 设置环境变量
# 4. 初始化开发配置
#
# 使用方法：
#   bash scripts/dev/setup_mcp_dev.sh

set -e  # 遇到错误立即退出

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

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MCP_SERVER_DIR="$PROJECT_ROOT/mcp_server"
VENV_DIR="$PROJECT_ROOT/venv_mcp"

print_info "=== MCP Server 开发环境设置 ==="
print_info "项目根目录: $PROJECT_ROOT"
print_info "MCP Server 目录: $MCP_SERVER_DIR"
print_info "虚拟环境目录: $VENV_DIR"

# 检查Python版本
print_info "检查Python版本..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3 未安装，请先安装Python 3.8或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
print_info "当前Python版本: $PYTHON_VERSION"

# 检查Python版本是否满足要求 (>= 3.8)
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_success "Python版本满足要求"
else
    print_error "Python版本需要3.8或更高，当前版本: $PYTHON_VERSION"
    exit 1
fi

# 创建虚拟环境
print_info "创建Python虚拟环境..."
if [ -d "$VENV_DIR" ]; then
    print_warning "虚拟环境已存在，将重新创建"
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"
print_success "虚拟环境创建完成: $VENV_DIR"

# 激活虚拟环境
print_info "激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 升级pip
print_info "升级pip..."
pip install --upgrade pip

# 安装主项目依赖
print_info "安装主项目依赖..."
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    pip install -r "$PROJECT_ROOT/requirements.txt"
    print_success "主项目依赖安装完成"
else
    print_warning "主项目requirements.txt不存在，跳过"
fi

# 安装MCP Server专用依赖
print_info "安装MCP Server专用依赖..."
if [ -f "$MCP_SERVER_DIR/requirements.txt" ]; then
    pip install -r "$MCP_SERVER_DIR/requirements.txt"
    print_success "MCP Server依赖安装完成"
else
    print_error "MCP Server requirements.txt不存在"
    exit 1
fi

# 安装开发依赖
print_info "安装开发依赖..."
pip install pytest pytest-asyncio pytest-cov black isort flake8 mypy

# 设置环境变量文件
print_info "设置环境变量文件..."
ENV_FILE="$MCP_SERVER_DIR/.env"
ENV_EXAMPLE="$MCP_SERVER_DIR/env.example"

if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        print_success "已从示例文件创建 .env 配置"
    else
        print_warning "env.example 文件不存在，创建基本 .env 文件"
        cat > "$ENV_FILE" << EOF
# MCP Server 基本配置
MCP_SERVER_NAME="MIRIX MCP Server"
MCP_SERVER_VERSION="2.0.0"
MCP_TRANSPORT_TYPE="sse"
MCP_SSE_HOST="0.0.0.0"
MCP_SSE_PORT=18002
MCP_LOG_LEVEL="INFO"
MCP_DEBUG=true
MIRIX_BACKEND_URL="http://localhost:8000"
EOF
    fi
else
    print_info ".env 文件已存在，跳过创建"
fi

# 创建启动脚本
print_info "创建开发启动脚本..."
DEV_START_SCRIPT="$PROJECT_ROOT/scripts/dev/start_mcp_dev.sh"
cat > "$DEV_START_SCRIPT" << 'EOF'
#!/bin/bash
# MCP Server 开发模式启动脚本

set -e

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv_mcp"

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "虚拟环境不存在，请先运行 setup_mcp_dev.sh"
    exit 1
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 启动MCP Server
echo "启动 MCP Server 开发模式..."
python -m mcp_server --debug --log-level DEBUG "$@"
EOF

chmod +x "$DEV_START_SCRIPT"
print_success "开发启动脚本创建完成: $DEV_START_SCRIPT"

# 创建测试脚本
print_info "创建测试脚本..."
TEST_SCRIPT="$PROJECT_ROOT/scripts/dev/test_mcp.sh"
cat > "$TEST_SCRIPT" << 'EOF'
#!/bin/bash
# MCP Server 测试脚本

set -e

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv_mcp"

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "虚拟环境不存在，请先运行 setup_mcp_dev.sh"
    exit 1
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 切换到项目根目录
cd "$PROJECT_ROOT"

echo "运行 MCP Server 测试..."

# 运行代码格式检查
echo "1. 代码格式检查..."
black --check mcp_server/ || (echo "代码格式不符合规范，运行 'black mcp_server/' 修复" && exit 1)

# 运行导入排序检查
echo "2. 导入排序检查..."
isort --check-only mcp_server/ || (echo "导入排序不正确，运行 'isort mcp_server/' 修复" && exit 1)

# 运行语法检查
echo "3. 语法检查..."
flake8 mcp_server/ --max-line-length=100 --ignore=E203,W503

# 运行类型检查
echo "4. 类型检查..."
mypy mcp_server/ --ignore-missing-imports

# 运行单元测试
echo "5. 单元测试..."
if [ -d "tests/mcp_server" ]; then
    pytest tests/mcp_server/ -v --cov=mcp_server
else
    echo "测试目录不存在，跳过单元测试"
fi

echo "所有测试通过！"
EOF

chmod +x "$TEST_SCRIPT"
print_success "测试脚本创建完成: $TEST_SCRIPT"

# 输出使用说明
print_success "=== MCP Server 开发环境设置完成 ==="
echo ""
print_info "使用方法："
echo "  1. 激活虚拟环境: source $VENV_DIR/bin/activate"
echo "  2. 启动开发服务器: bash scripts/dev/start_mcp_dev.sh"
echo "  3. 运行测试: bash scripts/dev/test_mcp.sh"
echo "  4. 配置文件: $MCP_SERVER_DIR/.env"
echo ""
print_info "开发服务器将在以下地址启动："
echo "  - SSE端点: http://localhost:18002/sse"
echo "  - 消息端点: http://localhost:18002/messages"
echo ""
print_warning "注意：请根据需要修改 $MCP_SERVER_DIR/.env 中的配置"
