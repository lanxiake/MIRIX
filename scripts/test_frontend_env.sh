#!/bin/bash

# ============================================================================
# 前端环境变量配置测试脚本
# ============================================================================
# 功能: 验证前端代码是否正确读取环境变量
# ============================================================================

set -e

echo "=================================================="
echo "前端环境变量配置测试"
echo "=================================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_passed() {
    echo -e "${GREEN}✓ $1${NC}"
}

test_failed() {
    echo -e "${RED}✗ $1${NC}"
}

test_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# 1. 检查源代码修改
echo "1. 检查源代码是否已修改..."
echo ""

# 检查 App.js
if grep -q "process.env.REACT_APP_BACKEND_URL" /opt/MIRIX/frontend/src/App.js; then
    test_passed "App.js 已使用环境变量"
else
    test_failed "App.js 仍然使用硬编码地址"
    exit 1
fi

# 检查 MemoryTreeVisualization.js
if grep -q "process.env.REACT_APP_BACKEND_URL" /opt/MIRIX/frontend/src/components/MemoryTreeVisualization.js; then
    test_passed "MemoryTreeVisualization.js 已使用环境变量"
else
    test_failed "MemoryTreeVisualization.js 仍然使用硬编码地址"
    exit 1
fi

echo ""

# 2. 检查 Dockerfile
echo "2. 检查 Dockerfile.frontend..."
echo ""

if grep -q "ARG REACT_APP_BACKEND_URL" /opt/MIRIX/Dockerfile.frontend; then
    test_passed "Dockerfile.frontend 包含构建参数"
else
    test_failed "Dockerfile.frontend 缺少构建参数"
    exit 1
fi

echo ""

# 3. 检查构建脚本
echo "3. 检查构建脚本..."
echo ""

if grep -q "REACT_APP_BACKEND_URL" /opt/MIRIX/scripts/build_and_push_images.sh; then
    test_passed "构建脚本支持环境变量"
else
    test_failed "构建脚本未支持环境变量"
    exit 1
fi

echo ""

# 4. 语法检查
echo "4. 验证语法..."
echo ""

# 检查 bash 脚本语法
if bash -n /opt/MIRIX/scripts/build_and_push_images.sh 2>/dev/null; then
    test_passed "构建脚本语法正确"
else
    test_failed "构建脚本语法错误"
    exit 1
fi

echo ""

# 5. 显示当前环境变量配置
echo "5. 当前环境变量配置..."
echo ""

if [ -f /opt/MIRIX/.env ]; then
    test_info "找到 .env 文件"
    echo ""
    echo "REACT_APP_BACKEND_URL 配置:"
    if grep -q "REACT_APP_BACKEND_URL" /opt/MIRIX/.env; then
        grep "REACT_APP_BACKEND_URL" /opt/MIRIX/.env
    else
        test_info "未在 .env 中配置 REACT_APP_BACKEND_URL（将使用默认值）"
    fi
    echo ""
    echo "REACT_APP_MCP_SSE_URL 配置:"
    if grep -q "REACT_APP_MCP_SSE_URL" /opt/MIRIX/.env; then
        grep "REACT_APP_MCP_SSE_URL" /opt/MIRIX/.env
    else
        test_info "未在 .env 中配置 REACT_APP_MCP_SSE_URL（将使用默认值）"
    fi
else
    test_info ".env 文件不存在，可以从 .env.registry.template 复制"
    echo ""
    echo "建议执行："
    echo "  cp /opt/MIRIX/.env.registry.template /opt/MIRIX/.env"
fi

echo ""

# 6. 显示构建命令示例
echo "6. 构建命令示例..."
echo ""

echo "方法1: 使用环境变量"
echo "------------------------------"
echo "export REACT_APP_BACKEND_URL=http://10.157.152.40:47283"
echo "export REACT_APP_MCP_SSE_URL=http://10.157.152.40:18002"
echo "./scripts/build_and_push_images.sh -c frontend -v v1.0.1"
echo ""

echo "方法2: 使用 .env 文件（推荐）"
echo "------------------------------"
echo "# 编辑 .env 文件，设置正确的地址"
echo "# 然后直接构建"
echo "./scripts/build_and_push_images.sh -c frontend -v v1.0.1"
echo ""

echo "方法3: 直接使用 docker build"
echo "------------------------------"
echo "docker build \\"
echo "  --build-arg REACT_APP_BACKEND_URL=http://10.157.152.40:47283 \\"
echo "  --build-arg REACT_APP_MCP_SSE_URL=http://10.157.152.40:18002 \\"
echo "  -f Dockerfile.frontend \\"
echo "  -t mirix-frontend:test \\"
echo "  ."
echo ""

# 7. 总结
echo "=================================================="
echo "测试总结"
echo "=================================================="
echo ""
test_passed "所有代码修改已完成"
test_passed "环境变量配置已就绪"
test_passed "可以开始构建镜像"
echo ""
test_info "详细文档请查看："
echo "  - frontend/ENV_CONFIG.md (配置说明)"
echo "  - FRONTEND_ENV_FIX.md (修复报告)"
echo ""
echo "=================================================="



