#!/bin/bash

# ============================================================================
# MIRIX 数据库迁移脚本
# ============================================================================
# 说明: 执行数据库迁移以更新 user_settings 表结构
# 使用: ./run_migration.sh [migration_file]
# ============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 数据库连接信息（从环境变量或默认值获取）
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_DB=${POSTGRES_DB:-mirix}
POSTGRES_USER=${POSTGRES_USER:-mirix}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-mirix123}

# 迁移文件路径
MIGRATION_FILE=${1:-"001_update_user_settings_table.sql"}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}MIRIX 数据库迁移${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "数据库主机: ${GREEN}${POSTGRES_HOST}:${POSTGRES_PORT}${NC}"
echo -e "数据库名称: ${GREEN}${POSTGRES_DB}${NC}"
echo -e "迁移文件: ${GREEN}${MIGRATION_FILE}${NC}"
echo ""

# 检查迁移文件是否存在
if [ ! -f "${SCRIPT_DIR}/${MIGRATION_FILE}" ]; then
    echo -e "${RED}错误: 迁移文件不存在: ${SCRIPT_DIR}/${MIGRATION_FILE}${NC}"
    exit 1
fi

# 检查数据库连接
echo -e "${YELLOW}正在检查数据库连接...${NC}"
export PGPASSWORD="${POSTGRES_PASSWORD}"
if ! psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}错误: 无法连接到数据库${NC}"
    echo -e "${RED}请确保数据库服务正在运行并且连接信息正确${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 数据库连接成功${NC}"
echo ""

# 创建备份
echo -e "${YELLOW}正在创建数据库备份...${NC}"
BACKUP_FILE="${SCRIPT_DIR}/backup_$(date +%Y%m%d_%H%M%S).sql"
if pg_dump -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" > "${BACKUP_FILE}"; then
    echo -e "${GREEN}✓ 备份已创建: ${BACKUP_FILE}${NC}"
else
    echo -e "${RED}警告: 备份创建失败，是否继续？ (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${YELLOW}迁移已取消${NC}"
        exit 1
    fi
fi
echo ""

# 执行迁移
echo -e "${YELLOW}正在执行数据库迁移...${NC}"
if psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f "${SCRIPT_DIR}/${MIGRATION_FILE}"; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ 迁移成功完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "备份文件: ${GREEN}${BACKUP_FILE}${NC}"
    echo -e "如果需要回滚，请使用以下命令:"
    echo -e "${YELLOW}psql -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} -d ${POSTGRES_DB} < ${BACKUP_FILE}${NC}"
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ 迁移失败！${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "如果需要回滚，请使用备份文件: ${YELLOW}${BACKUP_FILE}${NC}"
    exit 1
fi

# 清理环境变量
unset PGPASSWORD

