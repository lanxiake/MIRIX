.PHONY: install format lint test all check
.PHONY: docker-help docker-install docker-dev docker-dev-tools docker-logs docker-status
.PHONY: docker-stop docker-restart docker-rebuild docker-clean docker-health
.PHONY: docker-backup docker-restore docker-update docker-monitor docker-test

# Define variables
PYTHON = python3
POETRY = poetry
PYTEST = $(POETRY) run pytest
RUFF = $(POETRY) run ruff
PYRIGHT = $(POETRY) run pyright

# 颜色定义
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# Default target
all: format lint test

# ========================================
# 开发环境命令
# ========================================

# Install dependencies
install:
	$(POETRY) install

# Format code
format:
	$(RUFF) check --select I --fix
	$(RUFF) format

# Lint code
lint:
	$(RUFF) check --fix
	$(PYRIGHT) .

# Run tests
test:
	$(PYTEST)

# Run format, lint, and test
check: format lint test

# ========================================
# Docker 部署命令
# ========================================

# Docker 帮助信息
docker-help: ## 显示 Docker 部署帮助
	@echo "$(BLUE)MIRIX Docker 部署管理$(NC)"
	@echo ""
	@echo "$(GREEN)快速开始:$(NC)"
	@echo "  make docker-install    # 完整安装（生产环境）"
	@echo "  make docker-dev        # 开发环境启动"
	@echo "  make docker-logs       # 查看日志"
	@echo "  make docker-status     # 检查状态"
	@echo ""
	@echo "$(GREEN)可用命令:$(NC)"
	@echo "  $(YELLOW)docker-install$(NC)     生产环境部署"
	@echo "  $(YELLOW)docker-dev$(NC)         开发环境启动"
	@echo "  $(YELLOW)docker-dev-tools$(NC)   开发环境 + 工具"
	@echo "  $(YELLOW)docker-rebuild$(NC)     重新构建镜像"
	@echo "  $(YELLOW)docker-status$(NC)      查看服务状态"
	@echo "  $(YELLOW)docker-logs$(NC)        查看服务日志"
	@echo "  $(YELLOW)docker-health$(NC)      健康检查"
	@echo "  $(YELLOW)docker-stop$(NC)        停止服务"
	@echo "  $(YELLOW)docker-restart$(NC)     重启服务"
	@echo "  $(YELLOW)docker-clean$(NC)       清理数据"
	@echo "  $(YELLOW)docker-backup$(NC)      备份数据库"
	@echo "  $(YELLOW)docker-test$(NC)        测试连接"

# 检查 Docker 依赖
docker-check-deps:
	@echo "$(BLUE)检查 Docker 依赖...$(NC)"
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)错误: Docker 未安装$(NC)"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "$(RED)错误: Docker Compose 未安装$(NC)"; exit 1; }
	@echo "$(GREEN)依赖检查通过$(NC)"

# 环境设置
docker-setup-env:
	@echo "$(BLUE)设置环境变量...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(YELLOW)已创建 .env 文件，请编辑配置 API 密钥$(NC)"; \
		echo "$(YELLOW)编辑完成后重新运行命令$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)环境变量已配置$(NC)"

# 生产环境部署
docker-install: docker-check-deps docker-setup-env ## Docker 生产环境部署
	@echo "$(BLUE)开始生产环境部署...$(NC)"
	@./deploy.sh
	@echo "$(GREEN)部署完成！$(NC)"
	@echo ""
	@echo "$(GREEN)访问地址:$(NC)"
	@echo "  前端应用: http://localhost:18001"
	@echo "  API 文档: http://localhost:47283/docs"

# 开发环境
docker-dev: docker-check-deps docker-setup-env ## Docker 开发环境启动
	@echo "$(BLUE)启动开发环境...$(NC)"
	@./deploy.sh -d

# 开发环境 + 工具
docker-dev-tools: docker-check-deps docker-setup-env ## Docker 开发环境 + 工具
	@echo "$(BLUE)启动开发环境（包含工具）...$(NC)"
	@./deploy.sh -d --tools
	@echo ""
	@echo "$(GREEN)开发工具访问地址:$(NC)"
	@echo "  pgAdmin:    http://localhost:5050"
	@echo "  Redis 管理: http://localhost:8081"
	@echo "  邮件测试:   http://localhost:8025"

# 重新构建
docker-rebuild: ## Docker 重新构建并启动
	@echo "$(BLUE)重新构建镜像...$(NC)"
	@./deploy.sh -b

# 查看状态
docker-status: ## Docker 查看服务状态
	@echo "$(BLUE)服务状态:$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(BLUE)健康检查:$(NC)"
	@./health-check.sh

# 查看日志
docker-logs: ## Docker 查看服务日志
	@docker-compose logs --tail=100 -f

# 查看后端日志
docker-logs-backend: ## Docker 查看后端日志
	@docker-compose logs -f mirix-backend

# 查看前端日志
docker-logs-frontend: ## Docker 查看前端日志
	@docker-compose logs -f mirix-frontend

# 查看数据库日志
docker-logs-db: ## Docker 查看数据库日志
	@docker-compose logs -f postgres redis

# 健康检查
docker-health: ## Docker 运行健康检查
	@./health-check.sh

# 停止服务
docker-stop: ## Docker 停止所有服务
	@echo "$(YELLOW)停止服务...$(NC)"
	@docker-compose down
	@echo "$(GREEN)服务已停止$(NC)"

# 重启服务
docker-restart: ## Docker 重启所有服务
	@echo "$(YELLOW)重启服务...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)服务已重启$(NC)"

# 清理数据
docker-clean: ## Docker 清理所有数据和镜像
	@echo "$(RED)警告: 这将删除所有数据和镜像！$(NC)"
	@read -p "确认继续？ (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker-compose down -v --rmi all; \
		docker system prune -f; \
		echo "$(GREEN)清理完成$(NC)"; \
	else \
		echo "$(YELLOW)操作已取消$(NC)"; \
	fi

# 数据库备份
docker-backup: ## Docker 备份数据库
	@echo "$(BLUE)备份数据库...$(NC)"
	@mkdir -p backups
	@docker-compose exec postgres pg_dump -U mirix mirix > backups/mirix_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)数据库备份完成$(NC)"

# 数据库恢复
docker-restore: ## Docker 恢复数据库 (需要指定备份文件: make docker-restore FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)错误: 请指定备份文件$(NC)"; \
		echo "$(YELLOW)使用方法: make docker-restore FILE=backup.sql$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)恢复数据库...$(NC)"
	@docker-compose exec -T postgres psql -U mirix mirix < $(FILE)
	@echo "$(GREEN)数据库恢复完成$(NC)"

# 更新系统
docker-update: ## Docker 更新镜像并重启
	@echo "$(BLUE)更新系统...$(NC)"
	@docker-compose pull
	@docker-compose up -d
	@echo "$(GREEN)更新完成$(NC)"

# 性能监控
docker-monitor: ## Docker 实时监控资源使用
	@echo "$(BLUE)实时监控 (Ctrl+C 退出):$(NC)"
	@watch -n 2 'docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"'

# 测试连接
docker-test: ## Docker 测试服务连接
	@echo "$(BLUE)测试服务连接...$(NC)"
	@echo -n "后端 API: "
	@curl -sf http://localhost:47283/health >/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(RED)FAIL$(NC)"
	@echo -n "前端: "
	@curl -sf http://localhost:18001/health >/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(RED)FAIL$(NC)"
	@echo -n "MCP 服务: "
	@curl -sf http://localhost:18002/sse >/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(RED)FAIL$(NC)"

# 进入容器
docker-shell-backend: ## 进入后端容器
	@docker-compose exec mirix-backend bash

docker-shell-db: ## 进入数据库容器
	@docker-compose exec postgres psql -U mirix mirix

docker-shell-redis: ## 进入 Redis 容器
	@docker-compose exec redis redis-cli