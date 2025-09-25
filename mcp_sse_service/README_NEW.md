# MIRIX MCP 服务器

基于官方 MCP Python SDK 的标准 MCP 服务器实现，为 MIRIX 记忆管理系统提供 MCP 协议接口。

## 概述

这是 MIRIX 项目的 MCP (Model Context Protocol) 服务器实现，使用官方 Python SDK 重构，提供标准化的记忆管理工具和资源。

### 主要功能

- **记忆管理工具**：添加、搜索、聊天、档案管理
- **资源访问**：状态信息、记忆统计、系统监控
- **提示生成**：基于记忆上下文的智能提示
- **标准协议**：完全兼容 MCP 协议规范

## 快速开始

### 1. 环境准备

```bash
# 确保 MIRIX 后端正在运行
cd /opt/MIRIX
python main.py

# 进入 MCP 服务目录
cd mcp_sse_service

# 安装依赖
pip install mcp fastapi httpx pydantic-settings

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件设置正确的配置
```

### 2. 配置文件

创建或编辑 `.env` 文件：

```bash
# MIRIX 后端配置
MIRIX_BACKEND_URL=http://10.157.152.40:47283
MIRIX_BACKEND_TIMEOUT=30

# 用户配置
DEFAULT_USER_ID=default_user

# AI 模型配置
AI_MODEL=gemini-2.0-flash-thinking-exp

# 调试配置
DEBUG=false
LOG_LEVEL=INFO
```

### 3. 测试服务器

```bash
# 运行测试套件
python run_mcp_server.py --test

# 或直接运行测试
python test_mcp_server.py
```

### 4. 启动 MCP 服务器

```bash
# 标准模式（通过 stdio）
python run_mcp_server.py

# 调试模式
python run_mcp_server.py --debug

# 直接运行服务器
python server.py
```

## 架构设计

### 核心组件

```
mcp_sse_service/
├── server.py              # 主 MCP 服务器（基于 FastMCP）
├── config_simple.py       # 简化配置管理
├── mirix_client_simple.py # MIRIX 后端客户端
├── run_mcp_server.py      # 启动脚本
├── test_mcp_server.py     # 测试套件
└── .env.example           # 环境配置示例
```

### 重构改进

相比原有实现，新架构具有以下优势：

1. **标准化**：使用官方 MCP Python SDK
2. **简化**：移除冗余代码和复杂配置
3. **可维护性**：清晰的模块分离和职责划分
4. **稳定性**：完善的错误处理和日志机制
5. **兼容性**：完全兼容 MCP 协议规范

## MCP 工具

### 记忆管理工具

#### `memory_add`
添加记忆到 MIRIX 记忆系统。

**参数**：
- `content` (string): 记忆内容
- `memory_type` (string): 记忆类型（core, episodic, semantic, procedural, resource, knowledge_vault）
- `context` (string, 可选): 上下文信息

**使用场景**：
- 用户分享个人信息、偏好或重要事实
- 学习新知识或技能时存储关键信息
- 记录重要对话内容或决定
- 保存工作流程和步骤说明

#### `memory_search`
在用户记忆系统中搜索相关信息。

**参数**：
- `query` (string): 搜索查询
- `memory_types` (array, 可选): 要搜索的记忆类型
- `limit` (integer): 返回结果数量限制（默认 10）

**使用场景**：
- 用户询问之前讨论过的话题
- 需要回忆用户偏好和习惯
- 查找相关知识和经验
- 在回答问题前检索背景信息

#### `memory_chat`
发送消息给 MIRIX Agent 并自动管理记忆。

**参数**：
- `message` (string): 聊天消息
- `memorizing` (boolean): 是否自动记忆（默认 true）
- `image_uris` (array, 可选): 图片 URI 列表

**使用场景**：
- 进行需要记忆上下文的深度对话
- 讨论重要话题，希望 AI 记住关键信息
- 获取基于个人记忆的个性化回应
- AI 学习和适应用户偏好

#### `memory_get_profile`
获取用户的完整记忆档案概览。

**参数**：
- `memory_types` (array, 可选): 要获取的记忆类型

**使用场景**：
- 初次与用户交互时了解用户背景
- 全面了解用户偏好和特点
- 为用户提供个性化建议前的信息收集
- 定期回顾和更新对用户的了解

## MCP 资源

### `mirix://status`
获取 MIRIX 后端状态信息，包括连接状态、健康检查结果等。

### `mirix://memory/stats`
获取记忆系统统计信息，包括各类型记忆的数量和分布。

## MCP 提示

### `mirix_memory_prompt`
生成基于记忆上下文的系统提示。

**参数**：
- `context` (string): 对话上下文类型（默认 "general"）
- `user_question` (string, 可选): 用户问题

## 集成指南

### Claude Desktop 配置

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "mirix-memory": {
      "command": "python",
      "args": ["/opt/MIRIX/mcp_sse_service/run_mcp_server.py"],
      "cwd": "/opt/MIRIX/mcp_sse_service"
    }
  }
}
```

### 编程接口使用

```python
from mcp.client import ClientSession

# 连接到 MIRIX MCP 服务器
async with ClientSession() as session:
    # 添加记忆
    result = await session.call_tool("memory_add", {
        "content": "用户喜欢喝咖啡",
        "memory_type": "core",
        "context": "用户偏好"
    })

    # 搜索记忆
    memories = await session.call_tool("memory_search", {
        "query": "咖啡",
        "limit": 5
    })

    # 获取状态资源
    status = await session.read_resource("mirix://status")
```

## 故障排除

### 常见问题

1. **连接失败**
   - 确保 MIRIX 后端正在运行（端口 47283）
   - 检查 `MIRIX_BACKEND_URL` 配置
   - 验证网络连接

2. **工具调用失败**
   - 检查参数格式和类型
   - 确认记忆类型是有效值
   - 查看服务器日志获取详细错误信息

3. **性能问题**
   - 调整 `MIRIX_BACKEND_TIMEOUT` 设置
   - 检查后端服务器负载
   - 优化搜索查询的复杂度

### 调试模式

启用调试模式获取详细日志：

```bash
python run_mcp_server.py --debug
```

### 测试工具

运行完整测试套件：

```bash
python test_mcp_server.py
```

## 开发指南

### 扩展工具

在 `server.py` 中添加新工具：

```python
@mcp.tool()
async def new_tool(param: str) -> Dict[str, Any]:
    """新工具的描述"""
    # 实现逻辑
    return {"result": "success"}
```

### 添加资源

```python
@mcp.resource("mirix://new-resource")
async def new_resource() -> str:
    """新资源的描述"""
    # 获取资源数据
    return json.dumps(data, indent=2)
```

### 自定义提示

```python
@mcp.prompt()
async def custom_prompt(param: str = "default") -> List[Dict[str, Any]]:
    """自定义提示的描述"""
    return [
        {
            "role": "system",
            "content": f"Custom prompt with {param}"
        }
    ]
```

## 贡献指南

1. 遵循现有代码风格和注释规范
2. 添加适当的错误处理和日志
3. 更新文档和测试用例
4. 确保向后兼容性

## 许可证

本项目遵循 Apache License 2.0 许可证。

## 支持

如有问题或建议，请：
1. 查看本文档的故障排除部分
2. 运行测试套件诊断问题
3. 在项目仓库提交 issue
4. 联系 MIRIX 开发团队