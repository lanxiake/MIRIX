# MIRIX Docker 部署指南

## 概述

MIRIX 是一个基于多智能体架构的个人助理系统，支持六种专业化记忆组件。本指南将帮助您使用 Docker Compose 快速部署完整的 MIRIX 系统。

## 系统架构

MIRIX 系统包含以下服务：
- **PostgreSQL (pgvector)**: 主数据库，支持向量存储
- **Redis**: 缓存和会话管理
- **MIRIX Backend**: 核心 API 服务 (FastAPI)
- **MIRIX Frontend**: Web 用户界面 (React)
- **MCP Service**: 模型上下文协议服务 (SSE模式)

## 前置条件

### 系统要求
- Docker Engine 20.10+
- Docker Compose 2.0+
- 最低 4GB RAM
- 最低 10GB 可用磁盘空间

### 网络要求
- 端口 5432 (PostgreSQL)
- 端口 6380 (Redis)
- 端口 47283 (Backend API)
- 端口 18001 (Frontend)
- 端口 18002 (MCP Service)

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd MIRIX
```

### 2. 环境配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量文件
nano .env
```

**必须配置的环境变量：**
```bash
# LLM API 密钥 (至少配置一个)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 数据库密码 (可选，使用默认值)
POSTGRES_PASSWORD=mirix123
REDIS_PASSWORD=redis123

# 网络代理 (如需要)
HTTP_PROXY=http://your-proxy:port
HTTPS_PROXY=http://your-proxy:port
```

### 3. 启动服务
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f
```

### 4. 验证部署
```bash
# 检查后端 API
curl http://localhost:47283/health

# 检查前端
curl http://localhost:18001/health

# 检查 MCP 服务
curl http://localhost:18002/sse
```

## 详细部署步骤

### 步骤 1: 环境准备

1. **检查 Docker 版本**
```bash
docker --version
docker-compose --version
```

2. **创建数据目录** (可选)
```bash
mkdir -p ./data/{postgres,redis,mirix,logs}
```

### 步骤 2: 配置环境变量

编辑 `.env` 文件，配置以下关键参数：

#### LLM 服务配置
```bash
# 推荐使用 DeepSeek (默认模型)
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx

# 或使用其他提供商
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx
GOOGLE_AI_API_KEY=AIxxxxxxxxxxxxxxxxxxxxx
```

#### 数据库配置
```bash
# PostgreSQL 配置
POSTGRES_PASSWORD=your_secure_password

# Redis 配置
REDIS_PASSWORD=your_redis_password
```

#### 网络配置
```bash
# 如果需要代理访问 LLM API
HTTP_PROXY=http://proxy-server:port
HTTPS_PROXY=http://proxy-server:port
NO_PROXY=localhost,127.0.0.1,postgres,redis,mirix-frontend,mirix-mcp
```

### 步骤 3: 服务编排启动

1. **分步启动 (推荐)**
```bash
# 1. 启动数据库服务
docker-compose up -d postgres redis

# 等待数据库就绪
docker-compose logs postgres | grep "database system is ready"

# 2. 启动后端服务
docker-compose up -d mirix-backend

# 等待后端服务就绪
docker-compose logs mirix-backend | grep "Application startup complete"

# 3. 启动前端和 MCP 服务
docker-compose up -d mirix-frontend mirix-mcp
```

2. **一键启动**
```bash
# 同时启动所有服务 (依赖关系已配置)
docker-compose up -d
```

### 步骤 4: 服务验证

1. **健康检查**
```bash
# 检查所有服务状态
docker-compose ps

# 预期输出示例：
# mirix-postgres    Up (healthy)
# mirix-redis       Up (healthy)
# mirix-backend     Up (healthy)
# mirix-frontend    Up (healthy)
# mirix-mcp         Up (healthy)
```

2. **API 测试**
```bash
# 后端健康检查
curl -f http://localhost:47283/health
# 返回: {"status": "ok", "timestamp": "..."}

# 前端健康检查
curl -f http://localhost:18001/health
# 返回: {"status": "ok"}

# MCP SSE 连接测试
curl -f http://localhost:18002/sse
# 返回: SSE 连接响应
```

3. **日志检查**
```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs mirix-backend
docker-compose logs mirix-frontend
docker-compose logs mirix-mcp
```

## 访问应用

### Web 界面
- **前端应用**: http://localhost:18001
- **API 文档**: http://localhost:47283/docs
- **MCP SSE 端点**: http://localhost:18002/sse

### 数据库连接
- **PostgreSQL**: `localhost:5432`
  - 数据库: `mirix`
  - 用户: `mirix`
  - 密码: `mirix123` (或自定义)

- **Redis**: `localhost:6380`
  - 密码: `redis123` (或自定义)

## 常见问题排查

### 1. 服务启动失败

**检查端口占用**
```bash
# 检查端口是否被占用
netstat -tulpn | grep -E "(5432|6380|47283|18001|18002)"

# 停止占用端口的进程或修改 docker-compose.yml 中的端口映射
```

**检查内存使用**
```bash
# 检查系统内存
free -h
docker system df
```

### 2. 数据库连接失败

```bash
# 检查 PostgreSQL 日志
docker-compose logs postgres

# 手动连接测试
docker-compose exec postgres psql -U mirix -d mirix -c "SELECT version();"
```

### 3. LLM API 调用失败

```bash
# 检查后端日志中的 API 调用错误
docker-compose logs mirix-backend | grep -i "api\|error"

# 验证 API 密钥配置
docker-compose exec mirix-backend env | grep -E "(OPENAI|ANTHROPIC|GOOGLE|DEEPSEEK)"
```

### 4. 前端访问异常

```bash
# 检查前端服务状态
docker-compose logs mirix-frontend

# 检查后端 API 连通性
curl http://localhost:47283/health
```

## 生产环境配置

### 安全配置

1. **修改默认密码**
```bash
# 生成强密码
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
```

2. **网络安全**
```bash
# 仅在必要时暴露端口到外网
# 建议使用 nginx 反向代理
```

3. **数据备份**
```bash
# 配置定时备份
docker-compose exec postgres pg_dump -U mirix mirix > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 性能优化

1. **资源限制**
```yaml
# 在 docker-compose.yml 中添加资源限制
services:
  mirix-backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

2. **数据库优化**
```bash
# PostgreSQL 配置调优
# 编辑 postgresql.conf 或使用环境变量
```

## 开发环境

对于开发环境，可以使用开发配置：

```bash
# 使用开发配置启动
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 包含开发工具
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile tools up -d
```

开发环境包含：
- 代码热重载
- 调试端口
- pgAdmin (数据库管理)
- Redis Commander (Redis 管理)
- MailHog (邮件测试)

## 维护操作

### 服务管理
```bash
# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 更新服务
docker-compose pull && docker-compose up -d
```

### 数据管理
```bash
# 数据备份
docker-compose exec postgres pg_dump -U mirix mirix > mirix_backup.sql

# 数据恢复
docker-compose exec -T postgres psql -U mirix mirix < mirix_backup.sql

# 清理数据
docker-compose down -v  # 警告：会删除所有数据
```

### 日志管理
```bash
# 查看日志
docker-compose logs --tail=100 -f

# 清理日志
docker-compose down && docker system prune -f
```

## 支持与联系

如遇到问题：
1. 查看本指南的常见问题排查部分
2. 检查项目的 GitHub Issues
3. 查阅 CLAUDE.md 中的详细文档

---

**版本**: 1.0
**更新日期**: 2024-11-04
**适用版本**: MIRIX v1.0+