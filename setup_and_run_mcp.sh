#!/bin/bash
"""
MCP 服务器本地启动脚本

这个脚本会：
1. 检查 Python 环境
2. 安装必要的依赖
3. 启动 MCP 服务器
"""

echo "🔧 MIRIX MCP 服务器本地启动脚本"
echo "=================================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo "📋 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ 找到 Python: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ 未找到 Python3，请先安装 Python 3.8+${NC}"
    exit 1
fi

# 检查是否在项目目录
if [ ! -f "mcp_server/main.py" ]; then
    echo -e "${RED}❌ 请在 /opt/MIRIX 目录下运行此脚本${NC}"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "🔨 创建虚拟环境..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 虚拟环境创建成功${NC}"
    else
        echo -e "${RED}❌ 虚拟环境创建失败${NC}"
        exit 1
    fi
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "⬆️  升级 pip..."
pip install --upgrade pip > /dev/null 2>&1

# 安装依赖
echo "📦 安装 MCP 服务器依赖..."
if [ -f "mcp_server/requirements.txt" ]; then
    pip install -r mcp_server/requirements.txt
else
    # 手动安装核心依赖
    echo "安装核心依赖包..."
    pip install fastapi uvicorn httpx pydantic-settings mcp
fi

# 检查 MIRIX 后端连接（可选）
echo "🔗 检查后端连接..."
BACKEND_URL="http://localhost:47283"
if curl -s --connect-timeout 3 "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ MIRIX 后端服务可用${NC}"
    export MIRIX_BACKEND_URL="$BACKEND_URL"
else
    echo -e "${YELLOW}⚠️  MIRIX 后端服务不可用，使用默认配置${NC}"
    export MIRIX_BACKEND_URL="http://localhost:47283"
fi

# 设置环境变量
export MCP_SSE_HOST="0.0.0.0"
export MCP_SSE_PORT="18002" 
export MCP_LOG_LEVEL="INFO"
export MCP_DEBUG="true"

echo ""
echo "🚀 启动 MCP 服务器..."
echo "=================================================="
echo -e "${BLUE}📡 服务将运行在: http://localhost:18002${NC}"
echo -e "${BLUE}📡 SSE 端点: http://localhost:18002/sse${NC}"
echo -e "${YELLOW}💡 按 Ctrl+C 停止服务器${NC}"
echo ""

# 启动服务器
python3 start_mcp_local.py

echo ""
echo "👋 MCP 服务器已停止"
