# MIRIX MCP 服务使用指南

## 概述

MIRIX MCP (Model Context Protocol) 服务器是一个基于 MCP 协议的智能记忆管理系统，为 AI 应用提供持久化的记忆能力。通过标准化的 MCP 接口，您可以轻松地将 MIRIX 的记忆功能集成到任何支持 MCP 协议的 AI 客户端中。

### 核心特性

- **🧠 智能记忆管理**: 支持六种记忆类型的分类存储和检索
- **🔍 高效搜索**: 基于语义理解的智能记忆搜索
- **💬 个性化对话**: 基于记忆的上下文感知对话
- **📊 用户档案**: 自动生成和维护用户的完整记忆档案
- **🔌 标准协议**: 完全兼容 MCP 2024-11-05 协议规范
- **🚀 高性能**: 异步处理，支持并发请求

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

### 1. 环境要求

- Python 3.8+
- 支持 MCP 协议的客户端（如 Claude Desktop、Cline 等）
- MIRIX 后端服务（默认运行在 `http://10.157.152.40:47283`）

### 2. 基本配置

创建配置文件 `.env`：

```bash
# MCP 服务器配置
MCP_SERVER_NAME="MIRIX MCP Server"
MCP_SERVER_VERSION="1.0.0"
MCP_TRANSPORT_TYPE="stdio"

# MIRIX 后端配置
MIRIX_BACKEND_URL="http://10.157.152.40:47283"
MIRIX_BACKEND_TIMEOUT=30

# 记忆管理配置
MCP_DEFAULT_USER_ID="default_user"
MCP_MEMORY_SEARCH_LIMIT=10

# 日志配置
MCP_LOG_LEVEL="INFO"
MCP_DEBUG=false
```

### 3. 启动服务

#### 方式一：直接运行（stdio 模式）
```bash
cd /opt/MIRIX
python -m mcp_server.server
```

#### 方式二：作为模块导入
```python
import asyncio
from mcp_server.server import run_stdio_server

# 启动 stdio 服务器
asyncio.run(run_stdio_server())
```

#### 方式三：SSE 模式（用于 Web 集成）
```python
import asyncio
from mcp_server.server import run_sse_server

# 启动 SSE 服务器（监听 18002 端口）
asyncio.run(run_sse_server())
```

### 4. 客户端配置示例

#### Claude Desktop 配置
在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "mirix-memory": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/opt/MIRIX"
    }
  }
}
```

#### Cline 配置
在 Cline 设置中添加 MCP 服务器：

```json
{
  "name": "MIRIX Memory",
  "command": ["python", "-m", "mcp_server.server"],
  "cwd": "/opt/MIRIX"
}
```

## 核心功能

### 1. 记忆添加 (memory_add)

向记忆系统添加新信息，支持多种记忆类型的分类存储。

**基本用法：**
```json
{
  "tool": "memory_add",
  "arguments": {
    "content": "用户喜欢喝咖啡，特别是拿铁",
    "memory_type": "core",
    "context": "用户偏好"
  }
}
```

### 2. 记忆搜索 (memory_search)

在记忆系统中搜索相关信息，支持语义搜索和类型过滤。

**基本用法：**
```json
{
  "tool": "memory_search",
  "arguments": {
    "query": "用户的编程偏好",
    "memory_types": ["core", "semantic"],
    "limit": 5
  }
}
```

### 3. 记忆聊天 (memory_chat)

基于记忆进行个性化对话，支持多模态输入和记忆更新。

**基本用法：**
```json
{
  "tool": "memory_chat",
  "arguments": {
    "message": "你好，今天天气怎么样？",
    "memorizing": true
  }
}
```

### 4. 获取记忆档案 (memory_get_profile)

获取用户的完整记忆档案概览，包含个人信息、偏好、统计数据等。

**基本用法：**
```json
{
  "tool": "memory_get_profile",
  "arguments": {
    "memory_types": ["core", "semantic"]
  }
}
```

## 工作流程示例

### 典型的记忆管理流程

1. **初始化了解用户**
   ```json
   {
     "tool": "memory_get_profile",
     "arguments": {}
   }
   ```

2. **添加新的用户信息**
   ```json
   {
     "tool": "memory_add",
     "arguments": {
       "content": "用户是一名 Python 开发者，专注于 AI 应用开发",
       "memory_type": "core",
       "context": "职业信息"
     }
   }
   ```

3. **搜索相关记忆**
   ```json
   {
     "tool": "memory_search",
     "arguments": {
       "query": "Python 开发经验",
       "memory_types": ["core", "semantic", "procedural"],
       "limit": 10
     }
   }
   ```

4. **进行个性化对话**
   ```json
   {
     "tool": "memory_chat",
     "arguments": {
       "message": "能推荐一些 Python AI 开发的最佳实践吗？",
       "memorizing": true
     }
   }
   ```

## 响应格式

所有工具都返回标准化的响应格式：

```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    // 具体的返回数据
  },
  "metadata": {
    "timestamp": "2024-01-01T12:00:00Z",
    "tool_name": "memory_add",
    "execution_time": 0.123
  }
}
```

## 下一步

- [安装和配置指南](./INSTALLATION_GUIDE.md) - 详细的安装和配置说明
- [API 参考文档](./API_REFERENCE.md) - 完整的 API 文档和参数说明
- [使用示例](./USAGE_EXAMPLES.md) - 实际可执行的代码示例
- [故障排除指南](./TROUBLESHOOTING.md) - 常见问题和解决方案

---

**版本**: 1.0.0  
**更新时间**: 2024-01-01  
**维护团队**: MIRIX MCP Server Team