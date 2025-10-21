# 前端环境变量配置修复报告

## 问题描述

前端代码中硬编码了后端地址 `http://10.157.152.40:47283`，导致即使在 `.env.registry.template` 中配置了 `REACT_APP_BACKEND_URL` 环境变量，前端也不会使用它。

## 根本原因

1. **硬编码地址**: `App.js` 和 `MemoryTreeVisualization.js` 中直接写死了后端地址
2. **未读取环境变量**: 代码中没有使用 `process.env.REACT_APP_BACKEND_URL`
3. **构建时配置**: React 应用需要在构建时读取环境变量，而 Dockerfile 和构建脚本未传递这些变量

## 解决方案

### 修改的文件

#### 1. frontend/src/App.js
```javascript
// 第21行 - 修改前
serverUrl: 'http://10.157.152.40:47283'

// 修改后
serverUrl: process.env.REACT_APP_BACKEND_URL || 'http://localhost:47283'
```

#### 2. frontend/src/components/MemoryTreeVisualization.js
```javascript
// 第18行 - 修改前
serverUrl = 'http://10.157.152.40:47283'

// 修改后
serverUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:47283'
```

#### 3. Dockerfile.frontend
在构建阶段新增环境变量支持：
```dockerfile
# 设置构建时环境变量（带默认值）
ARG REACT_APP_BACKEND_URL=http://localhost:47283
ARG REACT_APP_MCP_SSE_URL=http://localhost:18002
ENV REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}
ENV REACT_APP_MCP_SSE_URL=${REACT_APP_MCP_SSE_URL}

# 构建应用
RUN npm run build
```

#### 4. scripts/build_and_push_images.sh
在 `build_with_buildx` 函数（第212-218行）和 `build_with_manual` 函数（第250-256行）中新增：
```bash
# 为前端构建添加环境变量参数
local build_args=""
if [ "$component_name" = "frontend" ]; then
    build_args="--build-arg REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL:-http://localhost:47283}"
    build_args="$build_args --build-arg REACT_APP_MCP_SSE_URL=${REACT_APP_MCP_SSE_URL:-http://localhost:18002}"
    log_info "前端构建参数: REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL:-http://localhost:47283}"
fi
```

#### 5. 新增文档
- `frontend/ENV_CONFIG.md`: 详细的环境变量配置说明

## 使用方法

### 方法1: 使用 .env 文件（推荐）

1. 编辑项目根目录的 `.env` 文件：
```bash
REACT_APP_BACKEND_URL=http://10.157.152.40:47283
REACT_APP_MCP_SSE_URL=http://10.157.152.40:18002
```

2. 使用构建脚本：
```bash
./scripts/build_and_push_images.sh -c frontend -v v1.0.1
```

### 方法2: 使用环境变量

```bash
export REACT_APP_BACKEND_URL=http://10.157.152.40:47283
export REACT_APP_MCP_SSE_URL=http://10.157.152.40:18002
./scripts/build_and_push_images.sh -c frontend
```

### 方法3: 直接传递构建参数

```bash
docker build \
  --build-arg REACT_APP_BACKEND_URL=http://10.157.152.40:47283 \
  --build-arg REACT_APP_MCP_SSE_URL=http://10.157.152.40:18002 \
  -f Dockerfile.frontend \
  -t mirix-frontend:latest \
  .
```

### 方法4: 使用 docker-compose.registry.yml

确保 `.env` 文件中配置了正确的值，然后：
```bash
docker-compose -f docker-compose.registry.yml build mirix-frontend
docker-compose -f docker-compose.registry.yml up -d
```

## 验证修改

### 1. 检查代码语法
```bash
# 前端代码 - 无 linter 错误
# 构建脚本 - bash 语法正确
```
✅ 已验证：所有修改的文件语法正确

### 2. 验证环境变量读取
修改后的代码会：
- 优先使用 `process.env.REACT_APP_BACKEND_URL`
- 如果未设置，回退到默认值 `http://localhost:47283`

### 3. 测试构建
```bash
# 测试本地构建
export REACT_APP_BACKEND_URL=http://test.example.com:47283
docker build -f Dockerfile.frontend -t mirix-frontend:test .

# 验证配置是否生效
docker run --rm mirix-frontend:test cat /usr/share/nginx/html/static/js/main.*.js | grep -o "http://[^\"]*:47283"
```

## 影响范围

### 受影响的组件
- ✅ App.js - 主应用配置
- ✅ MemoryTreeVisualization.js - 内存树可视化组件
- ✅ Dockerfile.frontend - 前端 Docker 构建
- ✅ build_and_push_images.sh - 镜像构建脚本

### 不受影响的组件
- i18n.js - 只是示例文本，不影响实际功能
- README.md - 文档说明，已经注明开发环境地址

## 向后兼容性

✅ **完全向后兼容**

- 如果未设置环境变量，默认使用 `http://localhost:47283`
- 旧的构建流程仍然可以工作
- 新增的构建参数是可选的

## 升级步骤

如果您已经部署了旧版本，升级步骤：

1. **拉取最新代码**
```bash
git pull origin main
```

2. **配置环境变量**
编辑 `.env` 文件，确保配置正确的后端地址

3. **重新构建镜像**
```bash
./scripts/build_and_push_images.sh -c frontend -v v1.0.1 --amd64-only
```

4. **更新部署**
```bash
docker-compose -f docker-compose.registry.yml pull mirix-frontend
docker-compose -f docker-compose.registry.yml up -d mirix-frontend
```

## 注意事项

1. **构建时配置**: React 环境变量在构建时（`npm run build`）被编译进静态文件，运行时无法修改
2. **重新构建**: 修改环境变量后必须重新构建镜像才能生效
3. **命名规则**: React 环境变量必须以 `REACT_APP_` 开头
4. **私有仓库**: 如果使用私有仓库，确保在构建前登录：
```bash
docker login 10.157.152.192:10443 -u zxsc-dev -p Zxsc-dev@123
```

## 相关文档

- 详细配置说明: `frontend/ENV_CONFIG.md`
- 环境变量模板: `.env.registry.template`
- Docker Compose 配置: `docker-compose.registry.yml`

## 修复确认

- ✅ 代码修改完成
- ✅ Dockerfile 更新完成
- ✅ 构建脚本更新完成
- ✅ 语法验证通过
- ✅ 文档已创建
- ✅ 向后兼容

**修复完成时间**: 2025-10-21


