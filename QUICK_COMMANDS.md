# MIRIX Docker 快速命令参考

## 🚀 快速部署（3 步）

```bash
# 1. 配置环境
cp .env.registry.template .env
nano .env  # 添加 API Keys

# 2. 创建数据目录
mkdir -p data/postgres

# 3. 启动服务
docker-compose -f docker-compose.registry.yml up -d
```

## 📦 镜像管理

```bash
# 查看所有 MIRIX 镜像
docker images | grep mirix

# 拉取最新镜像
docker-compose -f docker-compose.registry.yml pull

# 删除旧镜像
docker image prune -f
```

## 🔧 服务管理

```bash
# 启动
docker-compose -f docker-compose.registry.yml up -d

# 停止
docker-compose -f docker-compose.registry.yml stop

# 重启
docker-compose -f docker-compose.registry.yml restart

# 删除（保留数据）
docker-compose -f docker-compose.registry.yml down

# 删除（包括数据）
docker-compose -f docker-compose.registry.yml down -v
```

## 📊 监控和日志

```bash
# 查看状态
docker-compose -f docker-compose.registry.yml ps

# 查看所有日志
docker-compose -f docker-compose.registry.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.registry.yml logs -f mirix-backend
docker-compose -f docker-compose.registry.yml logs -f mirix-frontend
docker-compose -f docker-compose.registry.yml logs -f mirix-mcp-sse
docker-compose -f docker-compose.registry.yml logs -f postgres
docker-compose -f docker-compose.registry.yml logs -f redis

# 查看最近 100 行日志
docker-compose -f docker-compose.registry.yml logs --tail=100
```

## 🔍 调试

```bash
# 进入后端容器
docker-compose -f docker-compose.registry.yml exec mirix-backend bash

# 进入数据库
docker-compose -f docker-compose.registry.yml exec postgres psql -U mirix -d mirix

# 进入 Redis
docker-compose -f docker-compose.registry.yml exec redis redis-cli -a redis123

# 检查网络
docker network inspect mirix_mirix-network

# 查看容器资源使用
docker stats
```

## 🔄 更新镜像

```bash
# 1. 拉取新镜像
docker-compose -f docker-compose.registry.yml pull

# 2. 重新创建容器
docker-compose -f docker-compose.registry.yml up -d

# 3. 清理旧镜像
docker image prune -f
```

## 🏗️ 重新构建

```bash
# 构建所有组件
./scripts/build_and_push_images.sh \
  -n mirix \
  -v v1.0.0 \
  -m manual \
  --amd64-only

# 构建单个组件
./scripts/build_and_push_images.sh \
  -n mirix \
  -v v1.0.0 \
  -c backend \
  --amd64-only
```

## 🌐 访问地址

```
前端:        http://localhost:18001
后端 API:    http://localhost:47283
MCP SSE:     http://localhost:18002
PostgreSQL:  localhost:5432
Redis:       localhost:6380
```

## 🆘 常见问题

### 端口被占用
```bash
# 查找占用端口的进程
sudo lsof -i :18001
sudo lsof -i :47283

# 修改端口（编辑 docker-compose.registry.yml）
```

### 数据库连接失败
```bash
# 检查数据库状态
docker-compose -f docker-compose.registry.yml ps postgres

# 查看数据库日志
docker-compose -f docker-compose.registry.yml logs postgres

# 重启数据库
docker-compose -f docker-compose.registry.yml restart postgres
```

### 权限问题
```bash
# 修复数据目录权限
sudo chown -R $(whoami):$(whoami) data/
chmod -R 755 data/
```

---

**更多详细信息请查看**: 
- [DOCKER_BUILD_SUCCESS.md](DOCKER_BUILD_SUCCESS.md)
- [docs/DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md)
