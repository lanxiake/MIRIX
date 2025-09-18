# MIRIX MCP SSE 服务 API 文档

## 概述

MIRIX MCP SSE 服务提供基于 Server-Sent Events (SSE) 的 Model Context Protocol (MCP) 实现，允许客户端通过 HTTP 连接与 MIRIX 后端服务进行实时通信。

## 基础信息

- **服务地址**: http://localhost:8001
- **协议版本**: MCP 2024-11-05
- **传输方式**: HTTP + Server-Sent Events (SSE)
- **数据格式**: JSON

## 认证

所有 API 请求都需要在请求头中包含 API 密钥：

```http
X-API-Key: your_api_key_here
```

## 核心端点

### 1. 健康检查

检查服务是否正常运行。

```http
GET /health
```

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "uptime": 3600
}
```

### 2. 服务信息

获取服务的详细信息和能力。

```http
GET /info
```

**响应示例**:
```json
{
  "name": "MIRIX MCP SSE Service",
  "version": "1.0.0",
  "protocol_version": "2024-11-05",
  "capabilities": {
    "tools": true,
    "resources": true,
    "prompts": true,
    "logging": true
  },
  "server_info": {
    "name": "mirix-mcp-sse",
    "version": "1.0.0"
  }
}
```

### 3. 统计信息

获取服务运行统计信息。

```http
GET /stats
```

**响应示例**:
```json
{
  "active_connections": 5,
  "total_connections": 150,
  "messages_sent": 1250,
  "messages_received": 980,
  "uptime": 7200,
  "memory_usage": "45.2MB",
  "cpu_usage": "12.5%"
}
```

## SSE 连接管理

### 1. 建立 SSE 连接

建立 Server-Sent Events 连接以接收实时消息。

```http
GET /sse/connect?session_id=your_session_id
Accept: text/event-stream
Cache-Control: no-cache
```

**查询参数**:
- `session_id` (可选): 会话标识符，如果不提供将自动生成

**响应头**:
```http
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
Access-Control-Allow-Origin: *
```

**SSE 事件格式**:
```
event: connected
data: {"session_id": "sess_123456", "timestamp": "2024-01-15T10:30:00Z"}

event: heartbeat
data: {"timestamp": "2024-01-15T10:30:30Z"}

event: message
data: {"id": "msg_001", "type": "response", "content": {...}}
```

### 2. 发送消息

通过 HTTP POST 向指定会话发送 MCP 消息。

```http
POST /sse/send/{session_id}
Content-Type: application/json
```

**请求体示例**:
```json
{
  "jsonrpc": "2.0",
  "id": "req_001",
  "method": "tools/list",
  "params": {}
}
```

**响应示例**:
```json
{
  "success": true,
  "message_id": "msg_001",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. 断开连接

主动断开 SSE 连接。

```http
DELETE /sse/disconnect/{session_id}
```

**响应示例**:
```json
{
  "success": true,
  "message": "Session disconnected successfully"
}
```

## MCP 协议端点

### 1. 工具管理

#### 列出可用工具

```http
GET /mcp/tools
```

**响应示例**:
```json
{
  "tools": [
    {
      "name": "search_memory",
      "description": "搜索记忆内容",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "搜索查询"
          }
        },
        "required": ["query"]
      }
    }
  ]
}
```

#### 调用工具

```http
POST /mcp/tools/call
Content-Type: application/json
```

**请求体示例**:
```json
{
  "name": "search_memory",
  "arguments": {
    "query": "Docker 部署"
  }
}
```

### 2. 资源管理

#### 列出可用资源

```http
GET /mcp/resources
```

#### 读取资源内容

```http
GET /mcp/resources/{resource_uri}
```

### 3. 提示管理

#### 列出可用提示

```http
GET /mcp/prompts
```

#### 获取提示内容

```http
GET /mcp/prompts/{prompt_name}
```

## 会话管理

### 1. 列出活跃会话

```http
GET /sessions
```

**响应示例**:
```json
{
  "sessions": [
    {
      "session_id": "sess_123456",
      "created_at": "2024-01-15T10:00:00Z",
      "last_activity": "2024-01-15T10:30:00Z",
      "message_count": 25,
      "client_info": {
        "user_agent": "Mozilla/5.0...",
        "ip_address": "192.168.1.100"
      }
    }
  ],
  "total": 1
}
```

### 2. 获取会话详情

```http
GET /sessions/{session_id}
```

### 3. 广播消息

向所有活跃会话广播消息。

```http
POST /sessions/broadcast
Content-Type: application/json
```

**请求体示例**:
```json
{
  "event": "announcement",
  "data": {
    "message": "系统将在 5 分钟后进行维护",
    "type": "warning"
  }
}
```

## MIRIX 后端集成

### 1. 发送消息到 MIRIX

```http
POST /mirix/message
Content-Type: application/json
```

**请求体示例**:
```json
{
  "content": "请帮我搜索关于 Docker 的记忆",
  "type": "user_message",
  "session_id": "sess_123456"
}
```

### 2. 获取 MIRIX 状态

```http
GET /mirix/status
```

## 错误处理

### 错误响应格式

```json
{
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": {
      "details": "Missing required parameter: session_id"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 常见错误代码

| 代码 | 名称 | 描述 |
|------|------|------|
| -32700 | Parse Error | JSON 解析错误 |
| -32600 | Invalid Request | 无效请求 |
| -32601 | Method Not Found | 方法不存在 |
| -32602 | Invalid Params | 无效参数 |
| -32603 | Internal Error | 内部错误 |
| -32000 | Server Error | 服务器错误 |

## 速率限制

为防止滥用，API 实施了速率限制：

- **默认限制**: 每分钟 60 请求
- **突发限制**: 10 请求
- **限制头部**:
  ```http
  X-RateLimit-Limit: 60
  X-RateLimit-Remaining: 45
  X-RateLimit-Reset: 1642248600
  ```

## WebSocket 升级 (实验性)

支持将 HTTP 连接升级为 WebSocket 以获得更好的性能：

```http
GET /ws/{session_id}
Connection: Upgrade
Upgrade: websocket
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
```

## 客户端示例

### JavaScript (浏览器)

```javascript
// 建立 SSE 连接
const eventSource = new EventSource('http://localhost:8001/sse/connect');

eventSource.onopen = function(event) {
    console.log('SSE 连接已建立');
};

eventSource.addEventListener('connected', function(event) {
    const data = JSON.parse(event.data);
    console.log('会话 ID:', data.session_id);
});

eventSource.addEventListener('message', function(event) {
    const message = JSON.parse(event.data);
    console.log('收到消息:', message);
});

// 发送消息
async function sendMessage(sessionId, message) {
    const response = await fetch(`http://localhost:8001/sse/send/${sessionId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'your_api_key_here'
        },
        body: JSON.stringify(message)
    });
    
    return response.json();
}
```

### Python

```python
import requests
import sseclient

# 建立 SSE 连接
def connect_sse():
    headers = {
        'Accept': 'text/event-stream',
        'X-API-Key': 'your_api_key_here'
    }
    
    response = requests.get(
        'http://localhost:8001/sse/connect',
        headers=headers,
        stream=True
    )
    
    client = sseclient.SSEClient(response)
    
    for event in client.events():
        if event.event == 'message':
            message = json.loads(event.data)
            print(f"收到消息: {message}")

# 发送消息
def send_message(session_id, message):
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': 'your_api_key_here'
    }
    
    response = requests.post(
        f'http://localhost:8001/sse/send/{session_id}',
        headers=headers,
        json=message
    )
    
    return response.json()
```

## 配置选项

服务可通过环境变量进行配置：

```env
# 服务配置
MCP_SSE_HOST=0.0.0.0
MCP_SSE_PORT=8001
MCP_SSE_LOG_LEVEL=INFO

# SSE 配置
SSE_HEARTBEAT_INTERVAL=30
SSE_MAX_CONNECTIONS=1000
SSE_CONNECTION_TIMEOUT=300

# 速率限制
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=10
```

## 监控和调试

### 1. 启用调试日志

```env
MCP_SSE_DEBUG=true
MCP_SSE_LOG_LEVEL=DEBUG
```

### 2. 健康检查端点

```http
GET /health/detailed
```

### 3. 指标端点

```http
GET /metrics
```

返回 Prometheus 格式的指标数据。

## 安全考虑

1. **API 密钥**: 始终使用强 API 密钥
2. **HTTPS**: 生产环境中使用 HTTPS
3. **CORS**: 配置适当的 CORS 策略
4. **速率限制**: 启用速率限制防止滥用
5. **日志记录**: 记录所有 API 访问以便审计

## 故障排除

### 常见问题

1. **连接超时**
   - 检查防火墙设置
   - 验证服务是否正在运行
   - 检查网络连接

2. **认证失败**
   - 验证 API 密钥是否正确
   - 检查请求头格式

3. **消息丢失**
   - 检查 SSE 连接状态
   - 验证会话 ID 是否有效
   - 查看服务器日志

### 调试命令

```bash
# 检查服务状态
curl http://localhost:8001/health

# 测试 SSE 连接
curl -N -H "Accept: text/event-stream" http://localhost:8001/sse/connect

# 查看服务日志
docker-compose logs -f mirix-mcp-sse
```