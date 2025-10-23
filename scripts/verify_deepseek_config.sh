#!/bin/bash

# ============================================================================
# MIRIX DeepSeek 配置验证脚本
# ============================================================================
# 说明: 验证 DeepSeek 配置是否正确
# 使用: ./scripts/verify_deepseek_config.sh
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}MIRIX DeepSeek 配置验证${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

PASS_COUNT=0
FAIL_COUNT=0

# 检查函数
check_item() {
    local description="$1"
    local command="$2"
    local expected="$3"
    
    echo -e "${YELLOW}检查: ${description}${NC}"
    
    if eval "$command" | grep -q "$expected"; then
        echo -e "${GREEN}✓ 通过${NC}"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗ 失败${NC}"
        echo -e "${RED}  预期包含: ${expected}${NC}"
        ((FAIL_COUNT++))
    fi
    echo ""
}

# 1. 检查数据库表结构
echo -e "${BLUE}[1] 数据库表结构检查${NC}"
echo ""

if docker ps | grep -q "mirix-postgres"; then
    check_item "user_settings 表存在" \
        "docker exec mirix-postgres psql -U mirix -d mirix -c '\dt user_settings' 2>/dev/null" \
        "user_settings"
    
    check_item "chat_model 字段存在" \
        "docker exec mirix-postgres psql -U mirix -d mirix -c '\d user_settings' 2>/dev/null" \
        "chat_model"
    
    check_item "memory_model 字段存在" \
        "docker exec mirix-postgres psql -U mirix -d mirix -c '\d user_settings' 2>/dev/null" \
        "memory_model"
else
    echo -e "${RED}✗ PostgreSQL 容器未运行${NC}"
    ((FAIL_COUNT+=3))
    echo ""
fi

# 2. 检查代码配置
echo -e "${BLUE}[2] 代码配置检查${NC}"
echo ""

check_item "user_settings_manager.py 默认聊天模型" \
    "cat ${PROJECT_ROOT}/mirix/services/user_settings_manager.py" \
    'chat_model="deepseek-chat"'

check_item "user_settings_manager.py 默认记忆模型" \
    "cat ${PROJECT_ROOT}/mirix/services/user_settings_manager.py" \
    'memory_model="deepseek-chat"'

check_item "llm_config.py DeepSeek 配置" \
    "cat ${PROJECT_ROOT}/mirix/schemas/llm_config.py" \
    'deepseek-chat'

check_item "agent_wrapper.py 默认配置" \
    "cat ${PROJECT_ROOT}/mirix/agent/agent_wrapper.py" \
    'deepseek-chat'

# 3. 检查环境变量
echo -e "${BLUE}[3] 环境变量检查${NC}"
echo ""

check_item "docker-compose.yml DeepSeek API Key" \
    "cat ${PROJECT_ROOT}/docker-compose.yml" \
    "DEEPSEEK_API_KEY"

# 4. 检查配置文件
echo -e "${BLUE}[4] 配置文件检查${NC}"
echo ""

if [ -f "${PROJECT_ROOT}/mirix/configs/mirix_deepseek.yaml" ]; then
    echo -e "${GREEN}✓ mirix_deepseek.yaml 配置文件存在${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ mirix_deepseek.yaml 配置文件不存在${NC}"
    ((FAIL_COUNT++))
fi
echo ""

# 5. 检查服务状态
echo -e "${BLUE}[5] 服务状态检查${NC}"
echo ""

if docker ps | grep -q "mirix-backend"; then
    echo -e "${GREEN}✓ 后端服务正在运行${NC}"
    ((PASS_COUNT++))
    
    # 检查健康状态
    if docker ps --format "{{.Names}} {{.Status}}" | grep mirix-backend | grep -q "healthy"; then
        echo -e "${GREEN}✓ 后端服务健康${NC}"
        ((PASS_COUNT++))
    else
        echo -e "${YELLOW}⚠ 后端服务未显示健康状态（可能还在启动）${NC}"
    fi
else
    echo -e "${RED}✗ 后端服务未运行${NC}"
    ((FAIL_COUNT++))
fi
echo ""

# 6. 检查用户设置数据
echo -e "${BLUE}[6] 数据库数据检查${NC}"
echo ""

if docker ps | grep -q "mirix-postgres"; then
    USER_SETTINGS=$(docker exec mirix-postgres psql -U mirix -d mirix -t -c "SELECT chat_model, memory_model FROM user_settings LIMIT 1;" 2>/dev/null || echo "")
    
    if [ -n "$USER_SETTINGS" ]; then
        echo -e "${YELLOW}当前用户设置:${NC}"
        echo "$USER_SETTINGS"
        
        if echo "$USER_SETTINGS" | grep -q "deepseek-chat"; then
            echo -e "${GREEN}✓ 数据库中存在 deepseek-chat 配置${NC}"
            ((PASS_COUNT++))
        else
            echo -e "${YELLOW}⚠ 数据库中未找到 deepseek-chat 配置（可能还未创建用户）${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ 数据库中还没有用户设置记录${NC}"
    fi
else
    echo -e "${RED}✗ 无法检查数据库数据${NC}"
    ((FAIL_COUNT++))
fi
echo ""

# 汇总结果
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}验证结果汇总${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "通过检查: ${GREEN}${PASS_COUNT}${NC}"
echo -e "失败检查: ${RED}${FAIL_COUNT}${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！DeepSeek 配置正确。${NC}"
    echo ""
    echo -e "${YELLOW}下一步:${NC}"
    echo -e "  1. 打开前端: http://localhost:18001"
    echo -e "  2. 进入设置面板验证模型配置"
    echo -e "  3. 发送测试消息验证功能"
    exit 0
else
    echo -e "${RED}✗ 有 ${FAIL_COUNT} 项检查失败${NC}"
    echo ""
    echo -e "${YELLOW}建议操作:${NC}"
    
    if ! docker ps | grep -q "mirix-postgres"; then
        echo -e "  1. 启动数据库: ${BLUE}docker-compose up -d postgres${NC}"
    fi
    
    if ! grep -q "deepseek-chat" "${PROJECT_ROOT}/mirix/services/user_settings_manager.py" 2>/dev/null; then
        echo -e "  2. 执行配置脚本: ${BLUE}./scripts/configure_deepseek_default.sh${NC}"
    fi
    
    if ! docker exec mirix-postgres psql -U mirix -d mirix -c '\d user_settings' 2>/dev/null | grep -q "chat_model"; then
        echo -e "  3. 执行数据库迁移: ${BLUE}./scripts/migrate_user_settings.sh${NC}"
    fi
    
    if ! docker ps | grep -q "mirix-backend"; then
        echo -e "  4. 启动后端: ${BLUE}docker-compose up -d mirix-backend${NC}"
    else
        echo -e "  4. 重启后端: ${BLUE}docker-compose restart mirix-backend${NC}"
    fi
    
    echo ""
    exit 1
fi

