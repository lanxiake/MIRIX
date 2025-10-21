# 前端环境变量配置说明

## 概述

前端应用现在支持通过环境变量配置后端服务地址，无需修改源代码即可部署到不同环境。

## 环境变量

### REACT_APP_BACKEND_URL
- **说明**: MIRIX 后端服务地址
- **默认值**: `http://localhost:47283`
- **示例**: `http://10.157.152.40:47283`

### REACT_APP_MCP_SSE_URL
- **说明**: MCP SSE 服务地址
- **默认值**: `http://localhost:18002`
- **示例**: `http://10.157.152.40:18002`

## 使用方法

### 1. 本地开发环境

在项目根目录创建 `.env` 文件：

```bash
# .env
REACT_APP_BACKEND_URL=http://localhost:47283
REACT_APP_MCP_SSE_URL=http://localhost:18002
```

然后运行：
```bash
npm start
```

### 2. Docker 构建

#### 方法 A: 使用构建参数

```bash
docker build \
  --build-arg REACT_APP_BACKEND_URL=http://10.157.152.40:47283 \
  --build-arg REACT_APP_MCP_SSE_URL=http://10.157.152.40:18002 \
  -f Dockerfile.frontend \
  -t mirix-frontend:latest \
  .
```

#### 方法 B: 使用环境变量 + 构建脚本

设置环境变量：
```bash
export REACT_APP_BACKEND_URL=http://10.157.152.40:47283
export REACT_APP_MCP_SSE_URL=http://10.157.152.40:18002
```

使用构建脚本：
```bash
./scripts/build_and_push_images.sh -c frontend -v v1.0.0
```

构建脚本会自动读取环境变量并传递给 Docker 构建。

### 3. Docker Compose

在 `.env` 文件中配置：

```bash
# .env
REACT_APP_BACKEND_URL=http://10.157.152.40:47283
REACT_APP_MCP_SSE_URL=http://10.157.152.40:18002
```

在 `docker-compose.yml` 中使用：

```yaml
services:
  mirix-frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      args:
        REACT_APP_BACKEND_URL: ${REACT_APP_BACKEND_URL:-http://localhost:47283}
        REACT_APP_MCP_SSE_URL: ${REACT_APP_MCP_SSE_URL:-http://localhost:18002}
```

或者直接拉取预构建的镜像（推荐使用私有仓库部署）：

```bash
docker-compose -f docker-compose.registry.yml up -d
```

## 代码修改说明

### 修改的文件

1. **frontend/src/App.js** (第21行)
   ```javascript
   // 修改前
   serverUrl: 'http://10.157.152.40:47283'
   
   // 修改后
   serverUrl: process.env.REACT_APP_BACKEND_URL || 'http://localhost:47283'
   ```

2. **frontend/src/components/MemoryTreeVisualization.js** (第18行)
   ```javascript
   // 修改前
   serverUrl = 'http://10.157.152.40:47283'
   
   // 修改后
   serverUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:47283'
   ```

3. **Dockerfile.frontend** (新增构建参数)
   ```dockerfile
   ARG REACT_APP_BACKEND_URL=http://localhost:47283
   ARG REACT_APP_MCP_SSE_URL=http://localhost:18002
   ENV REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}
   ENV REACT_APP_MCP_SSE_URL=${REACT_APP_MCP_SSE_URL}
   ```

4. **scripts/build_and_push_images.sh** (新增环境变量支持)
   - 自动从环境变量读取配置
   - 传递构建参数给 Docker

## 注意事项

1. **React 环境变量规则**:
   - 必须以 `REACT_APP_` 开头
   - 在构建时（`npm run build`）被编译进静态文件
   - 运行时无法修改

2. **默认值回退**:
   - 如果未设置环境变量，会使用默认值 `http://localhost:47283`
   - 确保生产环境配置正确的环境变量

3. **重新构建要求**:
   - 修改环境变量后需要重新构建镜像
   - 不能在运行时动态修改（除非使用运行时配置方案）

## 验证配置

构建后验证环境变量是否生效：

```bash
# 查看构建的静态文件中的配置
docker run --rm mirix-frontend:latest cat /usr/share/nginx/html/static/js/main.*.js | grep -o "http://[^\"]*:47283"
```

## 故障排查

### 问题1: 前端仍然使用硬编码地址

**原因**: 使用了旧的镜像或未传递构建参数

**解决**:
```bash
# 删除旧镜像
docker rmi mirix-frontend:latest

# 重新构建
export REACT_APP_BACKEND_URL=http://your-backend-url:47283
./scripts/build_and_push_images.sh -c frontend
```

### 问题2: 构建时未读取环境变量

**原因**: Docker 构建时无法访问主机环境变量

**解决**: 使用 `--build-arg` 明确传递：
```bash
docker build --build-arg REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL ...
```

## 更多信息

- React 环境变量文档: https://create-react-app.dev/docs/adding-custom-environment-variables/
- Docker build-arg 文档: https://docs.docker.com/engine/reference/commandline/build/#build-arg


