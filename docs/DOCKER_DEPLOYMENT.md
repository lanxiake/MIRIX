# MIRIX Docker 镜像构建和部署指南

本文档介绍如何使用私有 Docker 仓库构建、推送和部署 MIRIX 项目。

## 目录

- [快速开始](#快速开始)
- [构建镜像](#构建镜像)
- [部署服务](#部署服务)
- [常见问题](#常见问题)

---

## 快速开始

### 1. 构建并推送镜像到私有仓库

```bash
# 构建所有组件的 latest 版本
./scripts/build_and_push_images.sh -n mirix -v latest

# 或者指定版本号
./scripts/build_and_push_images.sh -n mirix -v v1.0.0
```

### 2. 部署服务

```bash
# 创建环境变量文件
cp .env.registry.template .env

# 编辑 .env 文件，配置 API Keys 等信息
nano .env

# 创建数据目录
mkdir -p data/postgres

# 启动服务
docker-compose -f docker-compose.registry.yml up -d

# 查看日志
docker-compose -f docker-compose.registry.yml logs -f
```

---

## 构建镜像

### 脚本说明

`scripts/build_and_push_images.sh` 是用于构建和推送 MIRIX Docker 镜像的脚本。

### 基本用法

```bash
./scripts/build_and_push_images.sh [选项]
```

### 常用选项

| 选项 | 说明 | 示例 |
|------|------|------|
| `-n, --namespace` | 镜像命名空间 | `-n mirix` |
| `-v, --version` | 镜像版本标签 | `-v v1.0.0` |
| `-r, --registry` | Docker 仓库地址 | `-r 10.157.152.192:10443` |
| `-u, --username` | 仓库用户名 | `-u zxsc-dev` |
| `-w, --password` | 仓库密码 | `-w YourPassword` |
| `-m, --mode` | 构建模式 (buildx/manual) | `-m buildx` |
| `-c, --component` | 指定组件 | `-c backend` |
| `--amd64-only` | 只构建 AMD64 架构 | - |
| `--arm64-only` | 只构建 ARM64 架构 | - |
| `--no-push` | 构建但不推送 | - |
| `--insecure` | 允许不安全连接 | - |

### 使用示例

#### 1. 构建所有组件（推荐）

```bash
# 使用默认配置构建 latest 版本
./scripts/build_and_push_images.sh -n mirix -v latest

# 构建特定版本
./scripts/build_and_push_images.sh -n mirix -v v1.0.0
```

#### 2. 只构建指定组件

```bash
# 只构建后端
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 -c backend

# 只构建前端
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 -c frontend

# 只构建 MCP SSE 服务
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 -c mcp-sse
```

#### 3. 只构建特定架构

```bash
# 只构建 AMD64 架构
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 --amd64-only

# 只构建 ARM64 架构（如用于 Apple Silicon）
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 --arm64-only
```

#### 4. 使用 manual 模式（解决 buildx 问题）

如果遇到 buildx 相关问题，可以使用 manual 模式：

```bash
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 -m manual
```

#### 5. 使用不安全连接（HTTP 仓库）

如果私有仓库使用 HTTP 或自签名证书：

```bash
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 --insecure
```

#### 6. 本地构建不推送

仅构建镜像用于本地测试：

```bash
./scripts/build_and_push_images.sh -n mirix -v dev --no-push
```

### 构建模式说明

#### buildx 模式（推荐）

- 使用 Docker Buildx 一次性构建多架构镜像
- 速度更快，自动处理多平台
- 需要 Docker Buildx 支持

```bash
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 -m buildx
```

#### manual 模式

- 分别构建各架构，然后创建 manifest 清单
- 兼容性更好，适合老版本 Docker
- 构建时间较长

```bash
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 -m manual
```

---

## 部署服务

### 环境配置

#### 1. 创建环境变量文件

```bash
cp .env.registry.template .env
```

#### 2. 编辑 .env 文件

```bash
nano .env
```

必须配置的变量：

```env
# Docker 仓库配置
DOCKER_REGISTRY=10.157.152.192:10443
NAMESPACE=mirix
VERSION=v1.0.0  # 使用你构建的版本

# LLM API Keys（至少配置一个）
OPENAI_API_KEY=sk-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx
GOOGLE_AI_API_KEY=xxxxx

# 数据库密码（建议修改）
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_secure_password

# 前端访问地址（根据实际部署环境修改）
REACT_APP_BACKEND_URL=http://your-server-ip:47283
REACT_APP_MCP_SSE_URL=http://your-server-ip:18002
```

### 启动服务

#### 1. 创建数据目录

```bash
mkdir -p data/postgres
```

#### 2. 拉取镜像（可选）

```bash
# 如果需要先验证镜像是否可用
docker-compose -f docker-compose.registry.yml pull
```

#### 3. 启动所有服务

```bash
docker-compose -f docker-compose.registry.yml up -d
```

#### 4. 查看服务状态

```bash
# 查看所有服务状态
docker-compose -f docker-compose.registry.yml ps

# 查看实时日志
docker-compose -f docker-compose.registry.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.registry.yml logs -f mirix-backend
```

### 服务访问

服务启动后，可以通过以下地址访问：

- **前端界面**: http://localhost:18001
- **后端 API**: http://localhost:47283
- **MCP SSE 服务**: http://localhost:18002
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6380

### 服务管理

#### 停止服务

```bash
docker-compose -f docker-compose.registry.yml stop
```

#### 重启服务

```bash
# 重启所有服务
docker-compose -f docker-compose.registry.yml restart

# 重启特定服务
docker-compose -f docker-compose.registry.yml restart mirix-backend
```

#### 删除服务（保留数据）

```bash
docker-compose -f docker-compose.registry.yml down
```

#### 删除服务和数据

```bash
docker-compose -f docker-compose.registry.yml down -v
```

#### 更新镜像

```bash
# 拉取最新镜像
docker-compose -f docker-compose.registry.yml pull

# 重新创建容器
docker-compose -f docker-compose.registry.yml up -d
```

---

## 常见问题

### 1. Docker 仓库登录失败

**问题**: 无法登录到私有 Docker 仓库

**解决方案**:

```bash
# 手动登录测试
docker login 10.157.152.192:10443 -u zxsc-dev

# 如果使用 HTTP 仓库，需要配置 Docker daemon
sudo nano /etc/docker/daemon.json

# 添加以下内容
{
  "insecure-registries": ["10.157.152.192:10443"]
}

# 重启 Docker
sudo systemctl restart docker
```

### 2. 构建失败：Dockerfile 不存在

**问题**: 脚本提示 Dockerfile 不存在

**解决方案**:

确保各组件的 Dockerfile 存在：

- 后端: `/opt/MIRIX/Dockerfile.backend`
- 前端: `/opt/MIRIX/Dockerfile.frontend`
- MCP SSE: `/opt/MIRIX/Dockerfile.mcp-sse`

所有 Dockerfile 都位于项目根目录下。

### 3. 多架构构建失败

**问题**: buildx 构建多架构镜像失败

**解决方案**:

```bash
# 方案 1: 使用 manual 模式
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 -m manual

# 方案 2: 只构建当前架构
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 --amd64-only

# 方案 3: 更新 Docker Buildx
docker buildx install
```

### 4. 服务无法连接数据库

**问题**: 后端服务启动后报数据库连接错误

**解决方案**:

```bash
# 检查数据库容器状态
docker-compose -f docker-compose.registry.yml ps postgres

# 查看数据库日志
docker-compose -f docker-compose.registry.yml logs postgres

# 确保环境变量正确
cat .env | grep POSTGRES

# 等待数据库完全启动（健康检查通过）
docker-compose -f docker-compose.registry.yml up -d postgres
sleep 10
docker-compose -f docker-compose.registry.yml up -d mirix-backend
```

### 5. 前端无法连接后端

**问题**: 前端界面显示网络错误

**解决方案**:

检查 `.env` 文件中的前端配置：

```env
# 确保使用正确的外网地址（浏览器可访问）
REACT_APP_BACKEND_URL=http://your-server-ip:47283
REACT_APP_MCP_SSE_URL=http://your-server-ip:18002
```

注意：
- 容器内部通信使用服务名（如 `mirix-backend`）
- 浏览器访问需要使用主机 IP 或域名

### 6. 镜像推送超时或失败

**问题**: 推送镜像到仓库时超时或失败

**解决方案**:

```bash
# 1. 检查网络连接
curl -v http://10.157.152.192:10443/v2/

# 2. 增加 Docker 超时时间
export DOCKER_CLIENT_TIMEOUT=600
export COMPOSE_HTTP_TIMEOUT=600

# 3. 使用 manual 模式分步推送
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 -m manual

# 4. 单独推送各组件
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 -c backend
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 -c frontend
./scripts/build_and_push_images.sh -n mirix -v v1.0.0 -c mcp-sse
```

### 7. 权限问题

**问题**: 数据目录权限错误

**解决方案**:

```bash
# 修改数据目录权限
sudo chown -R $(whoami):$(whoami) data/
chmod -R 755 data/

# 或者使用 Docker 用户（通常是 UID 999）
sudo chown -R 999:999 data/postgres
```

### 8. 查看构建日志

```bash
# 构建日志保存在以下文件
cat docker_build_push_success.log  # 成功日志
cat docker_build_push_error.log    # 错误日志
```

---

## 高级配置

### 自定义网络配置

编辑 `docker-compose.registry.yml`，修改网络段：

```yaml
networks:
  mirix-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/16  # 自定义网段
```

### 持久化存储配置

默认情况下，PostgreSQL 数据存储在 `./data/postgres`。

如果需要更改存储位置：

```bash
# 在 .env 文件中设置
DATA_DIR=/your/custom/path
```

### 日志配置

调整日志级别：

```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### 资源限制

编辑 `docker-compose.registry.yml`，为服务添加资源限制：

```yaml
services:
  mirix-backend:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## 生产环境建议

1. **使用具体版本号**而非 `latest`
   ```bash
   VERSION=v1.0.0  # 在 .env 中指定
   ```

2. **修改默认密码**
   ```env
   POSTGRES_PASSWORD=your_secure_password
   REDIS_PASSWORD=your_secure_password
   ```

3. **配置 HTTPS**（使用 Nginx 反向代理）

4. **启用备份策略**
   ```bash
   # 定期备份 PostgreSQL
   docker exec mirix-postgres pg_dump -U mirix mirix > backup.sql
   ```

5. **监控服务健康状态**
   ```bash
   # 使用 healthcheck
   docker-compose -f docker-compose.registry.yml ps
   ```

6. **配置日志轮转**

---

## 相关文档

- [MIRIX 项目文档](../README.md)
- [Docker 部署文档](../docs/deployment.md)
- [API 文档](../docs/api.md)

---

## 支持

如遇问题，请检查：
1. 构建日志: `docker_build_push_error.log`
2. 服务日志: `docker-compose logs`
3. GitHub Issues
