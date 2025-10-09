#!/bin/bash
"""
简单的 MCP 服务器启动脚本

使用项目现有的 main.py 直接启动
"""

echo "🚀 启动 MIRIX MCP 服务器（简单模式）"
echo "======================================"

# 检查是否在正确的目录
if [ ! -f "mcp_server/main.py" ]; then
    echo "❌ 请在 /opt/MIRIX 目录下运行此脚本"
    exit 1
fi

# 设置环境变量
export MIRIX_BACKEND_URL="http://localhost:47283"
export MCP_SSE_HOST="0.0.0.0"
export MCP_SSE_PORT="18002"
export MCP_LOG_LEVEL="INFO"
export MCP_DEBUG="true"

echo "📋 配置信息:"
echo "  - 后端URL: $MIRIX_BACKEND_URL"
echo "  - 监听地址: $MCP_SSE_HOST:$MCP_SSE_PORT"
echo "  - 日志级别: $MCP_LOG_LEVEL"
echo ""

echo "🔗 服务端点:"
echo "  - SSE连接: http://localhost:18002/sse"
echo "  - 消息端点: http://localhost:18002/messages/"
echo ""

echo "💡 按 Ctrl+C 停止服务器"
echo "======================================"
echo ""

# 直接使用 Python 模块方式启动
python3 -m mcp_server --host 0.0.0.0 --port 18002 --debug
