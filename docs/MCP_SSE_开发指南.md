# MCP SSE 开发指南

## 概述

本文档总结了在开发和调试 MCP (Model Context Protocol) SSE (Server-Sent Events) 服务器过程中遇到的关键问题和解决方案，旨在为后续开发提供指导，避免重复犯错。

## 核心问题与解决方案

### 1. HTTP 405 "Method Not Allowed" 错误

#### 问题描述
在实现 MCP SSE 服务器时，遇到了 HTTP 405 错误，客户端无法向 SSE 端点发送 POST 请求。

#### 根本原因
MCP SSE 标准要求使用两个不同的端点：
- **SSE 连接端点**：用于 GET 请求，建立 Server-Sent Events 连接（通常为 `/sse`）
- **消息端点**：用于 POST 请求，客户端向服务器发送消息（通常为 `/messages`）

#### 错误的实现方式
```python
# 错误：两种请求类型使用同一个端点
app = Starlette(routes=[
    Route("/sse", endpoint=handle_sse),  # GET 请求
    Mount("/sse", app=sse.handle_post_message)  # POST 请求 - 冲突！
])
```

#### 正确的实现方式
```python
# 正确：分离 SSE 连接和消息端点
app = Starlette(routes=[
    Route(self.config.sse_endpoint, endpoint=self.handle_sse, methods=["GET"]),
    Mount(self.config.sse_message_endpoint, app=sse.handle_post_message)
])
```

#### 配置文件修改
在 `config.py` 中添加专门的消息端点配置：
```python
class Config:
    sse_endpoint: str = "/sse"  # SSE 连接端点
    sse_message_endpoint: str = "/messages"  # 消息端点
```

### 2. 路由配置最佳实践

#### 端点分离原则
- **GET `/sse`**：用于建立 SSE 连接，返回 `text/event-stream`
- **POST `/messages`**：用于接收客户端消息，返回 JSON 响应

#### 路由配置模板
```python
def setup_sse_routes(self):
    """设置 SSE 路由的标准模板"""
    return Starlette(routes=[
        # SSE 连接端点 - 仅支持 GET
        Route(
            self.config.sse_endpoint, 
            endpoint=self.handle_sse, 
            methods=["GET"]
        ),
        # 消息处理端点 - 支持 POST
        Mount(
            self.config.sse_message_endpoint, 
            app=self.sse_transport.handle_post_message
        )
    ])
```

### 3. 调试和测试策略

#### 分步测试方法
1. **测试 SSE 连接**：
   ```bash
   curl -v http://localhost:18002/sse
   ```
   期望结果：HTTP 200，`content-type: text/event-stream`

2. **测试消息端点**：
   ```bash
   curl -X POST http://localhost:18002/messages \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {...}}'
   ```
   期望结果：HTTP 202 或相应的 JSON 响应

#### 日志监控
确保服务器启动时正确显示两个端点：
```
INFO: SSE connection endpoint: /sse
INFO: SSE message endpoint: /messages
```

### 4. 常见错误模式

#### 错误模式 1：端点混淆
- **症状**：POST 请求返回 405 错误
- **原因**：将消息发送到 SSE 连接端点
- **解决**：检查客户端请求的 URL 路径

#### 错误模式 2：配置不一致
- **症状**：路由无法匹配
- **原因**：配置文件中的端点与代码中使用的不一致
- **解决**：统一使用配置文件中的端点定义

#### 错误模式 3：传输层初始化错误
- **症状**：服务器启动失败或消息处理异常
- **原因**：`SseServerTransport` 初始化时使用了错误的端点
- **解决**：确保传输层使用消息端点而非连接端点

## 开发检查清单

### 服务器配置检查
- [ ] 配置文件中定义了独立的 SSE 连接端点和消息端点
- [ ] 路由配置正确分离了 GET 和 POST 请求
- [ ] `SseServerTransport` 使用消息端点初始化
- [ ] 日志输出显示正确的端点信息

### 功能测试检查
- [ ] SSE 连接端点返回正确的事件流
- [ ] 消息端点能够接收和处理 POST 请求
- [ ] 客户端能够成功初始化连接
- [ ] 工具调用功能正常工作

### 代码质量检查
- [ ] 错误处理机制完善
- [ ] 日志记录详细且有用
- [ ] 配置参数化，避免硬编码
- [ ] 代码结构清晰，职责分离

## 推荐的开发流程

1. **设计阶段**：明确 SSE 连接和消息处理的端点分离
2. **配置阶段**：在配置文件中定义所有必要的端点
3. **实现阶段**：按照标准模板实现路由配置
4. **测试阶段**：使用分步测试方法验证功能
5. **部署阶段**：确保生产环境配置正确

## 参考资源

- [MCP 官方规范](https://spec.modelcontextprotocol.io/)
- [Server-Sent Events 标准](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Starlette 路由文档](https://www.starlette.io/routing/)

## 版本历史

- v1.0 (2025-01-26)：初始版本，包含 HTTP 405 错误解决方案