# MIRIX Docker 构建快速指南

## 📋 文件说明

已创建以下文件用于 Docker 镜像构建和部署：

1. **`scripts/build_and_push_images.sh`** - 镜像构建和推送脚本
2. **`docker-compose.registry.yml`** - 从私有仓库拉取镜像的部署配置
3. **`.env.registry.template`** - 环境变量配置模板
4. **`docs/DOCKER_DEPLOYMENT.md`** - 详细使用文档

## 🚀 快速开始

### 步骤 1: 构建并推送镜像

```bash
# 构建所有组件
./scripts/build_and_push_images.sh -n mirix -v v1.0.0

# 或只构建特定组件
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 -c backend
```

### 步骤 2: 部署服务

```bash
# 创建环境配置
cp .env.registry.template .env
nano .env  # 编辑配置，添加 API Keys

# 创建数据目录
mkdir -p data/postgres

# 启动服务
docker-compose -f docker-compose.registry.yml up -d

# 查看日志
docker-compose -f docker-compose.registry.yml logs -f
```

## 📖 详细文档

完整的使用说明、参数说明和故障排除请查看：

**[docs/DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md)**

## 🔧 常用命令

### 构建相关

```bash
# 构建所有组件（多架构）
./scripts/build_and_push_images.sh -n mirix -v latest

# 只构建 AMD64 架构
./scripts/build_and_push_images.sh -n mirix -v latest --amd64-only

# 使用 manual 模式（兼容性好）
./scripts/build_and_push_images.sh -n mirix -v latest -m manual

# 构建但不推送
./scripts/build_and_push_images.sh -n mirix -v dev --no-push
```

### 部署相关

```bash
# 启动所有服务
docker-compose -f docker-compose.registry.yml up -d

# 查看服务状态
docker-compose -f docker-compose.registry.yml ps

# 查看日志
docker-compose -f docker-compose.registry.yml logs -f

# 重启服务
docker-compose -f docker-compose.registry.yml restart

# 停止服务
docker-compose -f docker-compose.registry.yml down
```

## 🎯 项目结构说明

MIRIX 项目的 Dockerfile 都位于项目根目录：

```
/opt/MIRIX/
├── Dockerfile.backend      # 后端服务 Dockerfile
├── Dockerfile.frontend     # 前端应用 Dockerfile
├── Dockerfile.mcp-sse      # MCP SSE 服务 Dockerfile
├── docker-compose.registry.yml  # 私有仓库部署配置
└── scripts/
    └── build_and_push_images.sh  # 构建脚本
```

## ⚙️ 默认配置

- **Docker 仓库**: `10.157.152.192:10443`
- **命名空间**: `mirix`
- **版本标签**: `latest`（可自定义）
- **架构**: AMD64 + ARM64（多架构）
- **构建模式**: buildx（可切换为 manual）

## 🔑 环境变量（重要）

在 `.env` 文件中至少需要配置：

```env
# 至少配置一个 LLM API Key
OPENAI_API_KEY=sk-xxxxx
# 或
GOOGLE_AI_API_KEY=xxxxx
# 或
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 修改默认密码（生产环境）
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_secure_password
```

## 📦 构建的镜像

脚本会构建以下镜像：

1. `10.157.152.192:10443/mirix/backend:v1.0.0` - 后端 API 服务
2. `10.157.152.192:10443/mirix/frontend:v1.0.0` - 前端 Web 应用
3. `10.157.152.192:10443/mirix/mcp-sse:v1.0.0` - MCP SSE 服务

## 🌐 服务端口

部署后可通过以下端口访问：

- **前端**: http://localhost:18001
- **后端 API**: http://localhost:47283
- **MCP SSE**: http://localhost:18002
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6380

## ⚠️ 注意事项

1. **私有仓库认证**: 确保正确配置 Docker 仓库用户名和密码
2. **API Keys**: 必须至少配置一个 LLM API Key
3. **网络访问**: 确保可以访问私有 Docker 仓库
4. **磁盘空间**: 确保有足够空间存储镜像和数据
5. **防火墙**: 确保相关端口未被阻止

## 🐛 故障排除

### 登录失败

```bash
# 检查仓库连接
curl http://10.157.152.192:10443/v2/

# 手动登录测试
docker login 10.157.152.192:10443 -u zxsc-dev

# 配置不安全仓库（如需要）
sudo nano /etc/docker/daemon.json
# 添加: {"insecure-registries": ["10.157.152.192:10443"]}
sudo systemctl restart docker
```

### 构建失败

```bash
# 查看构建日志
cat docker_build_push_error.log

# 尝试 manual 模式
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 -m manual

# 只构建当前架构
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 --amd64-only
```

### 服务启动失败

```bash
# 查看详细日志
docker-compose -f docker-compose.registry.yml logs

# 检查数据库连接
docker-compose -f docker-compose.registry.yml exec mirix-backend env | grep DATABASE

# 重新创建服务
docker-compose -f docker-compose.registry.yml down
docker-compose -f docker-compose.registry.yml up -d
```

## 📚 更多帮助

```bash
# 查看脚本帮助
./scripts/build_and_push_images.sh --help

# 查看详细文档
cat docs/DOCKER_DEPLOYMENT.md
```

---

**祝您使用愉快！**
