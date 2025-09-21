# MIRIX MCP SSE 服务器使用说明

## 概述

MIRIX MCP SSE 服务器是一个支持 Server-Sent Events (SSE) 的 Model Context Protocol (MCP) 服务器，提供记忆管理功能。它支持两种运行模式：
1. **标准 stdio 模式**：符合 MCP 官方协议的标准实现
2. **SSE 模式**：通过 HTTP 和 SSE 提供服务，便于集成和调试

## 安装和启动

### 1. 标准 MCP 模式（推荐用于生产环境）

#### Claude Desktop 配置

在 Claude Desktop 的配置文件中添加以下配置：

```json
{
  "mcpServers": {
    "mirix-memory": {
      "command": "python3",
      "args": [
        "/opt/MIRIX/mcp_sse_service/run_mcp_server.py",
        "--backend-url", "http://localhost:47283",
        "--user-id", "user-00000000-0000-4000-8000-000000000000"
      ],
      "env": {
        "MIRIX_BACKEND_URL": "http://localhost:47283",
        "DEFAULT_USER_ID": "user-00000000-0000-4000-8000-000000000000"
      }
    }
  }
}
```

#### 命令行启动

```bash
cd /opt/MIRIX/mcp_sse_service

# 使用默认配置（stdio 模式）
python3 run_mcp_server.py

# 使用自定义配置
python3 run_mcp_server.py \
  --backend-url http://localhost:47283 \
  --user-id user-00000000-0000-4000-8000-000000000000 \
  --debug
```

### 2. SSE 模式（推荐用于开发和调试）

```bash
cd /opt/MIRIX/mcp_sse_service

# 启动 SSE 服务器
python3 run_mcp_server.py \
  --enable-sse \
  --sse-port 8081 \
  --sse-host localhost \
  --backend-url http://localhost:47283 \
  --user-id user-00000000-0000-4000-8000-000000000000 \
  --debug
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--backend-url` | MIRIX 后端服务 URL | `http://localhost:47283` |
| `--user-id` | 默认用户 ID | `default_user` |
| `--enable-sse` | 启用 SSE 服务器模式 | `false` |
| `--sse-port` | SSE 服务器端口 | `8080` |
| `--sse-host` | SSE 服务器主机地址 | `localhost` |
| `--debug` | 启用调试模式 | `false` |
| `--force-compatible` | 强制使用兼容版本 | `false` |
| `--test` | 运行测试模式 | `false` |

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MIRIX_BACKEND_URL` | MIRIX 后端服务 URL | `http://localhost:47283` |
| `DEFAULT_USER_ID` | 默认用户 ID | `default_user` |
| `DEBUG` | 调试模式 | `false` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

## API 端点

### SSE 模式下的 HTTP API

#### 基础端点
- `GET /` - 服务器信息
- `GET /health` - 健康检查

#### MCP 协议端点
- `POST /mcp/request` - MCP JSON-RPC 请求
- `GET /mcp/sse` - SSE 事件流

#### 工具端点（直接 HTTP 访问）
- `POST /tools/memory_add` - 添加记忆
- `POST /tools/memory_search` - 搜索记忆
- `POST /tools/memory_chat` - 记忆聊天
- `GET /tools/memory_get_profile` - 获取用户档案

#### 资源端点
- `GET /resources/status` - 获取后端状态
- `GET /resources/memory_stats` - 获取记忆统计

## 可用工具

### 1. memory_add
添加记忆到 MIRIX 记忆系统

**参数：**
- `content` (必需): 记忆内容
- `memory_type` (必需): 记忆类型（core, episodic, semantic, procedural, resource, knowledge_vault）
- `context` (可选): 上下文信息

**示例：**
```bash
curl -X POST http://localhost:8081/tools/memory_add \
  -H "Content-Type: application/json" \
  -d '{
    "content": "我喜欢编程，特别是Python和机器学习",
    "memory_type": "core",
    "context": "个人兴趣爱好"
  }'
```

### 2. memory_search
在用户记忆系统中搜索相关信息

**参数：**
- `query` (必需): 搜索查询
- `memory_types` (可选): 记忆类型数组
- `limit` (可选): 返回结果数量限制，默认 10

**示例：**
```bash
curl -X POST http://localhost:8081/tools/memory_search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "编程",
    "limit": 5
  }'
```

### 3. memory_chat
发送消息给 MIRIX Agent 并自动管理记忆

**参数：**
- `message` (必需): 聊天消息
- `memorizing` (可选): 是否自动记忆，默认 true
- `image_uris` (可选): 图片 URI 列表

**示例：**
```bash
curl -X POST http://localhost:8081/tools/memory_chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，我想了解一下我的兴趣爱好是什么？",
    "memorizing": true
  }'
```

### 4. memory_get_profile
获取用户的完整记忆档案概览

**参数：**
- `memory_types` (可选): 要获取的记忆类型数组

**示例：**
```bash
curl http://localhost:8081/tools/memory_get_profile
```

## MCP 协议示例

### 初始化
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {}
  }
}
```

### 列出工具
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

### 调用工具
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "memory_add",
    "arguments": {
      "content": "我热爱机器学习和深度学习技术",
      "memory_type": "semantic",
      "context": "技术兴趣"
    }
  }
}
```

## 测试

### 运行综合测试
```bash
cd /opt/MIRIX/mcp_sse_service
python3 test_mcp_comprehensive.py --url http://localhost:8081
```

### 手动测试 SSE 连接
```bash
curl -N http://localhost:8081/mcp/sse
```

## 故障排除

### 1. 连接失败
- 确保 MIRIX 后端服务正在运行（通常在端口 47283）
- 检查用户 ID 是否存在于后端系统中

### 2. 用户不存在错误
```bash
# 查看可用用户
curl http://localhost:47283/users

# 使用正确的用户 ID 重新启动服务
python3 run_mcp_server.py --user-id "实际的用户ID"
```

### 3. 端口冲突
- 更改 SSE 端口：`--sse-port 8082`
- 检查端口是否被占用：`netstat -tlnp | grep 8081`

### 4. 调试模式
启用详细日志：
```bash
python3 run_mcp_server.py --debug
```

## 集成示例

### 与 Claude Desktop 集成
将配置添加到 Claude Desktop 的 `claude_desktop_config.json` 文件中。

### 与其他 MCP 客户端集成
服务器完全符合 MCP 协议规范，可以与任何支持 MCP 的客户端集成。

## 性能说明

- 标准 stdio 模式：低延迟，适合生产环境
- SSE 模式：便于调试和开发，支持 HTTP API 直接访问
- 支持并发连接和请求处理
- 内置连接池和错误重试机制