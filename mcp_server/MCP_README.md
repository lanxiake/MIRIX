# MIRIX MCP 服务器 - SSE 模式

基于官方 MCP Python SDK 的 SSE (Server-Sent Events) 模式 MCP 服务器实现，为 MIRIX 记忆管理系统提供标准化的 MCP 协议接口。

## 概述

MIRIX MCP 服务器是一个专门为 SSE 模式优化的 MCP (Model Context Protocol) 服务器，提供完整的记忆管理功能。该服务器已经过重构，仅支持 SSE 传输模式，并专门针对 Docker 容器化部署进行了优化。

### 主要特性

- **🔥 纯 SSE 模式**：专门优化的 SSE 传输，提供更好的性能和稳定性
- **🐳 Docker 优先**：专为容器化部署设计，包含完整的健康检查
- **🧠 智能记忆管理**：支持六种记忆类型的分类存储和检索
- **🔍 高效搜索**：基于语义理解的智能记忆搜索
- **💬 个性化对话**：基于记忆的上下文感知对话
- **📊 用户档案**：自动生成和维护用户的完整记忆档案
- **🔌 标准协议**：完全兼容 MCP 2024-11-05 协议规范

### 记忆类型说明

| 类型 | 英文名称 | 描述 | 使用场景 |
|------|----------|------|----------|
| 核心记忆 | core | 基本个人信息、重要偏好 | 用户基本信息、核心偏好设置 |
| 情节记忆 | episodic | 具体事件、经历 | 对话历史、重要事件记录 |
| 语义记忆 | semantic | 知识、概念、事实 | 学习内容、知识点记录 |
| 程序记忆 | procedural | 技能、习惯、流程 | 工作流程、操作步骤 |
| 资源记忆 | resource | 文件、链接、工具 | 文档引用、工具推荐 |
| 知识库 | knowledge_vault | 结构化知识存储 | 专业知识、参考资料 |

## 快速开始

### 使用 Docker Compose（推荐）

这是最简单的部署方式，包含完整的 MIRIX 生态系统：

```bash
# 克隆项目
git clone https://github.com/Mirix-AI/MIRIX.git
cd MIRIX

# 启动完整服务栈
docker-compose up -d

# 检查 MCP 服务状态
docker-compose logs mirix-mcp
```

MCP 服务将在以下地址可用：
- **SSE 端点**: `http://localhost:18002/sse`
- **健康检查**: `http://localhost:18002/sse`（返回连接信息）

### 使用 Docker（单独部署）

如果只需要 MCP 服务器：

```bash
# 构建镜像
docker build -f Dockerfile.mcp -t mirix-mcp:latest .

# 运行容器
docker run -d \
  --name mirix-mcp \
  -p 18002:18002 \
  -e MIRIX_BACKEND_URL=http://your-backend:47283 \
  -e MCP_DEBUG=false \
  mirix-mcp:latest
```

### 开发模式

对于开发和测试：

```bash
# 进入项目目录
cd /opt/MIRIX

# 安装依赖
pip install -r requirements.txt

# 启动 MCP 服务器（SSE 模式）
python -m mcp_server --host 0.0.0.0 --port 18002 --debug
```

## 配置说明

### 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `MCP_TRANSPORT` | `sse` | 传输模式（固定为 sse） |
| `MCP_HOST` | `0.0.0.0` | 服务器监听地址 |
| `MCP_PORT` | `18002` | 服务器监听端口 |
| `MCP_DEBUG` | `false` | 调试模式开关 |
| `MIRIX_BACKEND_URL` | `http://localhost:47283` | MIRIX 后端服务地址 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### Docker Compose 配置

在 `docker-compose.yml` 中，MCP 服务配置如下：

```yaml
mirix-mcp:
  build:
    context: .
    dockerfile: Dockerfile.mcp
  container_name: mirix-mcp
  environment:
    MIRIX_BACKEND_URL: http://mirix-backend:47283
    MCP_TRANSPORT: sse
    MCP_HOST: 0.0.0.0
    MCP_PORT: 18002
    MCP_DEBUG: ${MCP_DEBUG:-false}
  ports:
    - "18002:18002"
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:18002/sse"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 15s
```

## MCP 工具

### 记忆管理工具

#### `memory_add`
添加记忆到 MIRIX 记忆系统。

**参数**：
- `content` (string): 记忆内容
- `memory_type` (string): 记忆类型（core, episodic, semantic, procedural, resource, knowledge_vault）
- `context` (string, 可选): 上下文信息

#### `memory_search`
在用户记忆系统中搜索相关信息。

**参数**：
- `query` (string): 搜索查询
- `memory_types` (array, 可选): 搜索的记忆类型列表
- `limit` (integer, 可选): 返回结果数量限制（默认 10）

#### `memory_chat`
基于记忆进行对话。

**参数**：
- `message` (string): 用户消息
- `context` (string, 可选): 对话上下文

#### `memory_get_profile`
获取用户的记忆档案。

**参数**：
- `user_id` (string, 可选): 用户ID（默认使用配置的用户ID）

## 客户端集成

### Claude Desktop 配置

在 Claude Desktop 的配置文件中添加：

```json
最简单的必要配置：
  {
    "mcpServers": {
      "mirix-mcp": {
        "url": "http://localhost:8080/sse",
        "userId": "zhangsan@company.com"  // 这个值会自动传递给所有工具调用
      }
    }
  }

完整配置：
  {
    "mcpServers": {
      "mirix-mcp": {
        "url": "http://localhost:8080/sse",
        "userId": "your_unique_user_id",  // 必须
        "backendUrl": "http://localhost:47283",  // 本地开发必须
        "userProfile": {  // 推荐
          "name": "张三",
          "email": "zhangsan@example.com",
          "language": "zh-CN",
          "timezone": "Asia/Shanghai",
          "preferences": {
            "memorySearchLimit": 10,
            "preferredMemoryTypes": ["core", "episodic", "semantic"]
          }
        },
        "timeout": 30,  // 可选
        "retryAttempts": 3,  // 可选
        "debug": false  // 可选，调试模式
      }
    }
  }

```

### 编程接口使用

```python
import httpx
import asyncio

async def test_mcp_server():
    """测试 MCP 服务器连接"""
    async with httpx.AsyncClient() as client:
        # 连接到 SSE 端点
        async with client.stream("GET", "http://localhost:18002/sse") as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    print(f"收到数据: {line}")
                elif line.startswith("event:"):
                    print(f"事件类型: {line}")

# 运行测试
asyncio.run(test_mcp_server())
```

## 健康检查和监控

### 健康检查端点

MCP 服务器提供内置的健康检查：

```bash
# 检查服务状态
curl -f http://localhost:18002/sse

# 预期响应：
# HTTP/1.1 200 OK
# Content-Type: text/event-stream
# event: endpoint
# data: /sse?session_id=xxx
```

### Docker 健康检查

Docker 容器包含自动健康检查：

```bash
# 查看容器健康状态
docker ps --format "table {{.Names}}\t{{.Status}}"

# 查看健康检查日志
docker inspect mirix-mcp --format='{{json .State.Health}}'
```

### 日志监控

```bash
# 查看实时日志
docker-compose logs -f mirix-mcp

# 查看最近的日志
docker-compose logs --tail=100 mirix-mcp
```

## 故障排除

### 常见问题

1. **连接失败**
   ```bash
   # 检查服务是否运行
   docker-compose ps mirix-mcp
   
   # 检查端口是否开放
   netstat -tlnp | grep 18002
   
   # 检查后端连接
   curl http://localhost:47283/health
   ```

2. **健康检查失败**
   ```bash
   # 查看详细错误
   docker-compose logs mirix-mcp
   
   # 手动测试健康检查
   curl -v http://localhost:18002/sse
   ```

3. **记忆操作失败**
   ```bash
   # 检查后端服务状态
   docker-compose logs mirix-backend
   
   # 验证数据库连接
   docker-compose exec postgres pg_isready -U mirix
   ```

### 调试模式

启用调试模式获取详细日志：

```bash
# 设置调试环境变量
export MCP_DEBUG=true

# 重启服务
docker-compose restart mirix-mcp

# 查看调试日志
docker-compose logs -f mirix-mcp
```

## 性能优化

### 资源配置

在生产环境中，建议调整以下配置：

```yaml
# docker-compose.yml
mirix-mcp:
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 512M
      reservations:
        cpus: '0.5'
        memory: 256M
```

### 网络优化

```yaml
# 使用专用网络
networks:
  mirix-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 版本信息

- **当前版本**: 2.0.0 (SSE Only)
- **MCP 协议版本**: 2024-11-05
- **Python 版本要求**: 3.8+
- **Docker 版本要求**: 20.10+

## 许可证

本项目基于 Apache License 2.0 开源协议。详见 [LICENSE](LICENSE) 文件。

## 支持和反馈

- **GitHub Issues**: [https://github.com/Mirix-AI/MIRIX/issues](https://github.com/Mirix-AI/MIRIX/issues)
- **Discord 社区**: [https://discord.gg/5HWyxJrh](https://discord.gg/5HWyxJrh)
- **邮件支持**: yuwang@mirix.io

---

**注意**: 此版本的 MCP 服务器仅支持 SSE 模式，不再支持 stdio 传输。如需 stdio 支持，请使用旧版本或联系开发团队。