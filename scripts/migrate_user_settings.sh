#!/bin/bash

# ============================================================================
# MIRIX 用户设置表迁移脚本 (Docker环境)
# ============================================================================
# 说明: 在Docker环境中执行数据库迁移以更新 user_settings 表结构
# 使用: ./scripts/migrate_user_settings.sh
# ============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}MIRIX 用户设置表迁移${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查是否在项目根目录
if [ ! -f "${PROJECT_ROOT}/docker-compose.yml" ]; then
    echo -e "${RED}错误: 未找到 docker-compose.yml 文件${NC}"
    echo -e "${RED}请确保在 MIRIX 项目根目录下运行此脚本${NC}"
    exit 1
fi

# 检查迁移文件是否存在
MIGRATION_FILE="${PROJECT_ROOT}/database/migrations/001_update_user_settings_table.sql"
if [ ! -f "${MIGRATION_FILE}" ]; then
    echo -e "${RED}错误: 迁移文件不存在: ${MIGRATION_FILE}${NC}"
    exit 1
fi

# 检查 Docker 容器是否运行
echo -e "${YELLOW}检查数据库容器状态...${NC}"
if ! docker ps | grep -q "mirix-postgres"; then
    echo -e "${RED}错误: PostgreSQL 容器未运行${NC}"
    echo -e "${YELLOW}正在启动 PostgreSQL 容器...${NC}"
    cd "${PROJECT_ROOT}"
    docker-compose up -d postgres
    echo -e "${YELLOW}等待数据库启动...${NC}"
    sleep 10
fi

# 获取数据库密码
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-mirix123}

echo -e "${GREEN}✓ 数据库容器正在运行${NC}"
echo ""

# 创建备份
echo -e "${YELLOW}正在创建数据库备份...${NC}"
BACKUP_DIR="${PROJECT_ROOT}/database/backups"
mkdir -p "${BACKUP_DIR}"
BACKUP_FILE="${BACKUP_DIR}/backup_before_user_settings_migration_$(date +%Y%m%d_%H%M%S).sql"

if docker exec mirix-postgres pg_dump -U mirix -d mirix > "${BACKUP_FILE}" 2>/dev/null; then
    echo -e "${GREEN}✓ 备份已创建: ${BACKUP_FILE}${NC}"
else
    echo -e "${RED}警告: 备份创建失败${NC}"
    echo -e "${YELLOW}是否继续执行迁移？ (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${YELLOW}迁移已取消${NC}"
        exit 1
    fi
fi
echo ""

# 显示将要执行的操作
echo -e "${YELLOW}将要执行的操作：${NC}"
echo -e "  1. 备份现有 user_settings 表数据"
echo -e "  2. 删除旧的 user_settings 表"
echo -e "  3. 创建新的 user_settings 表结构"
echo -e "  4. 迁移数据到新表（保留模型配置）"
echo ""
echo -e "${YELLOW}是否继续？ (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${YELLOW}迁移已取消${NC}"
    exit 1
fi
echo ""

# 执行迁移
echo -e "${YELLOW}正在执行数据库迁移...${NC}"
if docker exec -i mirix-postgres psql -U mirix -d mirix < "${MIGRATION_FILE}"; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ 迁移成功完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "完成的操作："
    echo -e "  ${GREEN}✓${NC} user_settings 表结构已更新"
    echo -e "  ${GREEN}✓${NC} 旧数据已迁移到新表结构"
    echo -e "  ${GREEN}✓${NC} 添加了新字段支持 chat_model 和 memory_model"
    echo ""
    echo -e "备份文件位置: ${GREEN}${BACKUP_FILE}${NC}"
    echo ""
    echo -e "${YELLOW}下一步操作：${NC}"
    echo -e "  1. 重启后端服务以应用更改："
    echo -e "     ${BLUE}docker-compose restart mirix-backend${NC}"
    echo -e "  2. 检查前端模型配置是否能正确保存"
    echo ""
    echo -e "${YELLOW}如果需要回滚，请使用以下命令:${NC}"
    echo -e "${BLUE}docker exec -i mirix-postgres psql -U mirix -d mirix < ${BACKUP_FILE}${NC}"
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ 迁移失败！${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "备份文件位置: ${YELLOW}${BACKUP_FILE}${NC}"
    echo -e ""
    echo -e "如果需要回滚，请使用以下命令:"
    echo -e "${BLUE}docker exec -i mirix-postgres psql -U mirix -d mirix < ${BACKUP_FILE}${NC}"
    exit 1
fi

