# MIRIX Docker 快速部署

本目录包含完整的 Docker Compose 部署解决方案，支持开发和生产环境。

## 🚀 快速开始

### 1. 使用部署脚本（推荐）
```bash
# 完整部署（生产环境）
./deploy.sh

# 开发环境
./deploy.sh -d

# 开发环境 + 工具
./deploy.sh -d --tools
```

### 2. 使用 Make 命令
```bash
# 查看可用命令
make docker-help

# 生产环境部署
make docker-install

# 开发环境部署
make docker-dev
```

### 3. 使用原生 Docker Compose
```bash
# 生产环境
docker-compose up -d

# 开发环境
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## 📋 环境配置

首次使用需要配置环境变量：

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（至少配置一个 LLM API 密钥）
nano .env
```

必需配置项：
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_AI_API_KEY` / `DEEPSEEK_API_KEY`

## 🔧 常用命令

### 服务管理
```bash
# 查看状态
make docker-status
./health-check.sh

# 查看日志
make docker-logs
docker-compose logs -f

# 重启服务
make docker-restart
```

### 数据管理
```bash
# 备份数据库
make docker-backup

# 恢复数据库
make docker-restore FILE=backup.sql
```

### 故障排查
```bash
# 健康检查
./health-check.sh

# 生成诊断报告
./health-check.sh --report

# 测试连接
make docker-test
```

## 🌐 访问地址

- **前端应用**: http://localhost:18001
- **API 文档**: http://localhost:47283/docs
- **MCP SSE**: http://localhost:18002/sse

## 📚 详细文档

完整部署指南请参阅：[DOCKER_DEPLOYMENT_GUIDE.md](./DOCKER_DEPLOYMENT_GUIDE.md)

## 🆘 获取帮助

```bash
# 部署脚本帮助
./deploy.sh --help

# Make 命令帮助
make docker-help

# 健康检查
./health-check.sh
```