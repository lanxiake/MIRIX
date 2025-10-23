#!/bin/bash

# ============================================================================
# MIRIX 配置 DeepSeek 为默认模型
# ============================================================================
# 说明: 自动修改代码以将 DeepSeek 设置为默认模型
# 使用: ./scripts/configure_deepseek_default.sh
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
echo -e "${BLUE}MIRIX - 配置 DeepSeek 为默认模型${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# DeepSeek 配置信息
DEEPSEEK_MODEL="deepseek-chat"
DEEPSEEK_ENDPOINT="https://api.deepseek.com/v1"
DEEPSEEK_API_KEY="sk-d44f718f3df9410ba5fd8e6164646777"

echo -e "${YELLOW}DeepSeek 配置信息：${NC}"
echo -e "  模型名称: ${GREEN}${DEEPSEEK_MODEL}${NC}"
echo -e "  API 端点: ${GREEN}${DEEPSEEK_ENDPOINT}${NC}"
echo -e "  API 密钥: ${GREEN}${DEEPSEEK_API_KEY}${NC}"
echo ""

# 检查是否在项目根目录
if [ ! -f "${PROJECT_ROOT}/docker-compose.yml" ]; then
    echo -e "${RED}错误: 未找到 docker-compose.yml 文件${NC}"
    exit 1
fi

# 创建备份目录
BACKUP_DIR="${PROJECT_ROOT}/backups/config_$(date +%Y%m%d_%H%M%S)"
mkdir -p "${BACKUP_DIR}"
echo -e "${YELLOW}创建配置文件备份: ${BACKUP_DIR}${NC}"

# 1. 备份并修改 user_settings_manager.py
echo -e "${YELLOW}[1/4] 修改用户设置管理器默认配置...${NC}"
USER_SETTINGS_FILE="${PROJECT_ROOT}/mirix/services/user_settings_manager.py"
cp "${USER_SETTINGS_FILE}" "${BACKUP_DIR}/user_settings_manager.py.bak"

# 替换默认聊天模型
sed -i 's/chat_model="gpt-4o-mini"/chat_model="deepseek-chat"/g' "${USER_SETTINGS_FILE}"
# 替换默认记忆模型
sed -i 's/memory_model="gemini-2.5-flash-lite"/memory_model="deepseek-chat"/g' "${USER_SETTINGS_FILE}"

echo -e "${GREEN}✓ 用户设置管理器已更新${NC}"

# 2. 修改 llm_config.py 添加 deepseek 默认配置
echo -e "${YELLOW}[2/4] 添加 DeepSeek 到 LLMConfig...${NC}"
LLM_CONFIG_FILE="${PROJECT_ROOT}/mirix/schemas/llm_config.py"
cp "${LLM_CONFIG_FILE}" "${BACKUP_DIR}/llm_config.py.bak"

# 检查是否已经存在 deepseek 配置
if grep -q "deepseek-chat" "${LLM_CONFIG_FILE}"; then
    echo -e "${YELLOW}  DeepSeek 配置已存在，跳过${NC}"
else
    # 在 default_config 方法中的 else 之前添加 deepseek 配置
    sed -i '/elif model_name == "letta":/i\        elif model_name == "deepseek-chat":\n            return cls(\n                model="deepseek-chat",\n                model_endpoint_type="openai",\n                model_endpoint="https://api.deepseek.com/v1",\n                model_wrapper=None,\n                context_window=64000,\n            )' "${LLM_CONFIG_FILE}"
    echo -e "${GREEN}✓ LLMConfig 已添加 DeepSeek 支持${NC}"
fi

# 3. 修改 agent_wrapper.py 的默认配置
echo -e "${YELLOW}[3/4] 修改 AgentWrapper 默认配置...${NC}"
AGENT_WRAPPER_FILE="${PROJECT_ROOT}/mirix/agent/agent_wrapper.py"
cp "${AGENT_WRAPPER_FILE}" "${BACKUP_DIR}/agent_wrapper.py.bak"

# 替换默认 LLM 配置
sed -i 's/LLMConfig.default_config("gpt-4o-mini")/LLMConfig.default_config("deepseek-chat")/g' "${AGENT_WRAPPER_FILE}"

echo -e "${GREEN}✓ AgentWrapper 已更新${NC}"

# 4. 添加环境变量到 docker-compose.yml
echo -e "${YELLOW}[4/4] 配置环境变量...${NC}"
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
cp "${DOCKER_COMPOSE_FILE}" "${BACKUP_DIR}/docker-compose.yml.bak"

# 检查是否已经存在 DEEPSEEK_API_KEY
if grep -q "DEEPSEEK_API_KEY" "${DOCKER_COMPOSE_FILE}"; then
    echo -e "${YELLOW}  DEEPSEEK_API_KEY 已存在，跳过${NC}"
else
    # 在 mirix-backend 服务的 environment 部分添加
    sed -i '/GOOGLE_AI_API_KEY:/a\      DEEPSEEK_API_KEY: '"${DEEPSEEK_API_KEY}" "${DOCKER_COMPOSE_FILE}"
    echo -e "${GREEN}✓ 环境变量已添加${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ 配置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}完成的修改：${NC}"
echo -e "  ${GREEN}✓${NC} 用户设置管理器默认模型已改为 deepseek-chat"
echo -e "  ${GREEN}✓${NC} LLMConfig 已添加 DeepSeek 支持"
echo -e "  ${GREEN}✓${NC} AgentWrapper 默认配置已更新"
echo -e "  ${GREEN}✓${NC} Docker Compose 环境变量已配置"
echo ""
echo -e "${YELLOW}备份文件位置：${NC}"
echo -e "  ${BLUE}${BACKUP_DIR}/${NC}"
echo ""
echo -e "${YELLOW}下一步操作：${NC}"
echo -e "  1. 执行数据库迁移（如果还未执行）："
echo -e "     ${BLUE}./scripts/migrate_user_settings.sh${NC}"
echo ""
echo -e "  2. 重启后端服务："
echo -e "     ${BLUE}cd ${PROJECT_ROOT}${NC}"
echo -e "     ${BLUE}docker-compose restart mirix-backend${NC}"
echo ""
echo -e "  3. 验证配置："
echo -e "     - 打开前端设置面板"
echo -e "     - 检查默认模型是否为 deepseek-chat"
echo -e "     - 发送测试消息验证功能"
echo ""
echo -e "${YELLOW}如需回滚配置：${NC}"
echo -e "  ${BLUE}cp ${BACKUP_DIR}/*.bak <原文件路径>${NC}"
echo ""

