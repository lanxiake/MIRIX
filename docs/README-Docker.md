# MIRIX Docker 部署指南

## 概述

MIRIX 项目采用微服务架构，支持 Docker 容器化部署。本指南将帮助您快速部署完整的 MIRIX 系统，包括：

- **mirix-backend**: Python FastAPI 后端服务
- **mirix-frontend**: React 前端应用
- **mirix-mcp-sse**: MCP 协议 SSE 服务
- **postgres**: PostgreSQL 数据库（带 pgvector 扩展）
- **redis**: Redis 缓存服务（可选）

## 系统要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

## 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd MIRIX
```

### 2. 环境配置

复制并编辑环境变量文件：

```bash
# 复制示例环境文件
cp .env.example .env

# 编辑环境变量（请根据实际情况修改）
# 主要配置项：
# - 数据库密码
# - JWT 密钥
# - API 密钥等
```

### 3. 构建和启动服务

```bash
# 构建所有服务
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 4. 验证部署

访问以下地址验证服务是否正常运行：

- **前端应用**: http://localhost:3000
- **后端 API**: http://localhost:8000/docs
- **MCP SSE 服务**: http://localhost:8001/health
- **数据库**: localhost:5432

## 服务详情

### 端口映射

| 服务 | 内部端口 | 外部端口 | 描述 |
|------|----------|----------|------|
| mirix-frontend | 80 | 3000 | React 前端应用 |
| mirix-backend | 8000 | 8000 | FastAPI 后端 API |
| mirix-mcp-sse | 8001 | 8001 | MCP SSE 服务 |
| postgres | 5432 | 5432 | PostgreSQL 数据库 |
| redis | 6379 | 6379 | Redis 缓存 |

### 数据持久化

以下目录将被持久化存储：

- `./data/postgres`: PostgreSQL 数据文件
- `./data/redis`: Redis 数据文件
- `./logs`: 应用日志文件

## 环境变量配置

### 核心配置

```env
# 数据库配置
POSTGRES_DB=mirix
POSTGRES_USER=mirix
POSTGRES_PASSWORD=your_secure_password

# JWT 配置
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# API 配置
API_V1_STR=/api/v1
PROJECT_NAME=MIRIX
```

### MCP SSE 服务配置

```env
# MCP SSE 服务
MCP_SSE_HOST=0.0.0.0
MCP_SSE_PORT=8001
MCP_SSE_LOG_LEVEL=INFO

# MIRIX 后端连接
MIRIX_BACKEND_URL=http://mirix-backend:8000
MIRIX_BACKEND_TIMEOUT=30

# SSE 配置
SSE_HEARTBEAT_INTERVAL=30
SSE_MAX_CONNECTIONS=1000
SSE_CONNECTION_TIMEOUT=300
```

## 开发模式

### 启动开发环境

```bash
# 启动开发模式（支持热重载）
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f mirix-backend
docker-compose logs -f mirix-frontend
docker-compose logs -f mirix-mcp-sse
```

### 进入容器调试

```bash
# 进入后端容器
docker-compose exec mirix-backend bash

# 进入前端容器
docker-compose exec mirix-frontend sh

# 进入数据库容器
docker-compose exec postgres psql -U mirix -d mirix
```

## 生产部署

### 1. 安全配置

在生产环境中，请确保：

- 修改所有默认密码
- 使用强 JWT 密钥
- 配置防火墙规则
- 启用 HTTPS（建议使用 Nginx 反向代理）

### 2. 性能优化

```bash
# 限制容器资源使用
docker-compose --compatibility up -d
```

### 3. 备份策略

```bash
# 数据库备份
docker-compose exec postgres pg_dump -U mirix mirix > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
docker-compose exec -T postgres psql -U mirix -d mirix < backup_file.sql
```

## 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :3000
   
   # 修改 docker-compose.yml 中的端口映射
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库服务状态
   docker-compose logs postgres
   
   # 验证数据库连接
   docker-compose exec postgres psql -U mirix -d mirix -c "SELECT version();"
   ```

3. **前端无法访问后端**
   ```bash
   # 检查网络连接
   docker-compose exec mirix-frontend ping mirix-backend
   
   # 检查 nginx 配置
   docker-compose exec mirix-frontend cat /etc/nginx/nginx.conf
   ```

4. **MCP SSE 服务连接问题**
   ```bash
   # 检查 MCP 服务状态
   curl http://localhost:8001/health
   
   # 测试 SSE 连接
   curl -N -H "Accept: text/event-stream" http://localhost:8001/sse/stream
   ```

### 日志分析

```bash
# 查看错误日志
docker-compose logs --tail=100 mirix-backend | grep ERROR

# 实时监控日志
docker-compose logs -f --tail=0 mirix-backend mirix-mcp-sse
```

### 健康检查

所有服务都配置了健康检查，可以通过以下命令查看：

```bash
# 查看服务健康状态
docker-compose ps

# 详细健康检查信息
docker inspect $(docker-compose ps -q mirix-backend) | grep -A 10 Health
```

## 扩展和自定义

### 添加新服务

1. 在 `docker-compose.yml` 中添加新服务定义
2. 创建对应的 Dockerfile
3. 配置网络和依赖关系
4. 更新环境变量配置

### 自定义配置

- 修改 `docker/nginx.conf` 自定义前端代理规则
- 编辑各服务的 Dockerfile 添加自定义依赖
- 调整 `docker-compose.yml` 中的资源限制

## 监控和维护

### 系统监控

建议集成以下监控工具：

- **Prometheus + Grafana**: 系统指标监控
- **ELK Stack**: 日志聚合和分析
- **Jaeger**: 分布式链路追踪

### 定期维护

```bash
# 清理未使用的镜像和容器
docker system prune -a

# 更新服务
docker-compose pull
docker-compose up -d

# 数据库维护
docker-compose exec postgres vacuumdb -U mirix -d mirix --analyze --verbose
```

## 支持和贡献

如果您在部署过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查项目的 Issues 页面
3. 提交新的 Issue 并提供详细的错误信息

欢迎提交 Pull Request 来改进部署配置和文档！