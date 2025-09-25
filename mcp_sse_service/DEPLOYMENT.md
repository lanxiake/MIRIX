# MIRIX MCP 服务器部署指南

本指南将帮助您快速部署和配置 MIRIX MCP 服务器。

## 🚀 快速部署

### 1. 环境检查

确保您的系统满足以下要求：

- Python 3.8+
- MIRIX 后端正在运行（端口 47283）
- 基本的 Python 包：`httpx` （通常已安装）

### 2. 启动 MIRIX 后端

```bash
# 在 MIRIX 项目根目录
cd /opt/MIRIX
python3 main.py
```

确保服务运行在 `http://10.157.152.40:47283`

### 3. 配置 MCP 服务器

```bash
# 进入 MCP 服务目录
cd /opt/MIRIX/mcp_sse_service

# 复制环境配置（可选）
cp .env.example .env

# 编辑配置（如果需要自定义）
# nano .env
```

### 4. 测试连接

```bash
# 运行测试套件
python3 run_mcp_server.py --test
```

您应该看到类似输出：

```
🔬 MIRIX MCP 服务器测试套件
==================================================
⚙️  配置信息:
   - MIRIX 后端: http://10.157.152.40:47283
   - 默认用户: default_user
   - AI 模型: gemini-2.0-flash-thinking-exp
   - 调试模式: False

==================== MIRIX 客户端连接 ====================
🔄 测试 MIRIX 客户端连接...
✅ MIRIX 客户端连接成功
🏥 健康检查: ✅ 正常

🎯 总计: 3/3 个测试通过
🎉 所有测试通过！MCP 服务器已准备就绪。
```

### 5. 启动 MCP 服务器

```bash
# 启动服务器（自动选择兼容版本）
python3 run_mcp_server.py

# 或强制使用兼容版本
python3 run_mcp_server.py --force-compatible

# 调试模式
python3 run_mcp_server.py --debug
```

## 🔧 集成配置

### Claude Desktop 配置

在 Claude Desktop 的配置文件中添加 MIRIX MCP 服务器：

**macOS/Linux:** `~/.config/claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mirix-memory": {
      "command": "python3",
      "args": ["/opt/MIRIX/mcp_sse_service/run_mcp_server.py"],
      "cwd": "/opt/MIRIX/mcp_sse_service",
      "env": {
        "MIRIX_BACKEND_URL": "http://10.157.152.40:47283",
        "DEFAULT_USER_ID": "your_user_id"
      }
    }
  }
}
```

### 配置选项

环境变量配置（`.env` 文件或系统环境变量）：

```bash
# MIRIX 后端配置
MIRIX_BACKEND_URL=http://10.157.152.40:47283    # MIRIX 后端 URL
MIRIX_BACKEND_TIMEOUT=30                    # 连接超时时间（秒）

# 用户配置
DEFAULT_USER_ID=default_user                # 默认用户 ID

# AI 模型配置
AI_MODEL=gemini-2.0-flash-thinking-exp      # 使用的 AI 模型

# 调试配置
DEBUG=false                                 # 是否启用调试模式
LOG_LEVEL=INFO                             # 日志级别
```

## 🛠️ 可用工具

重构后的 MCP 服务器提供以下工具：

### 1. memory_add
添加记忆到 MIRIX 记忆系统

**参数：**
- `content` (必需): 记忆内容
- `memory_type` (必需): 记忆类型 (core/episodic/semantic/procedural/resource/knowledge_vault)
- `context` (可选): 上下文信息

**示例：**
```json
{
  "name": "memory_add",
  "arguments": {
    "content": "用户喜欢喝咖啡",
    "memory_type": "core",
    "context": "用户偏好"
  }
}
```

### 2. memory_search
搜索用户记忆

**参数：**
- `query` (必需): 搜索查询
- `memory_types` (可选): 记忆类型数组
- `limit` (可选): 结果数量限制，默认 10

**示例：**
```json
{
  "name": "memory_search",
  "arguments": {
    "query": "咖啡",
    "memory_types": ["core", "episodic"],
    "limit": 5
  }
}
```

### 3. memory_chat
与 MIRIX Agent 对话

**参数：**
- `message` (必需): 聊天消息
- `memorizing` (可选): 是否自动记忆，默认 true
- `image_uris` (可选): 图片 URI 数组

**示例：**
```json
{
  "name": "memory_chat",
  "arguments": {
    "message": "我今天学习了什么？",
    "memorizing": false
  }
}
```

### 4. memory_get_profile
获取用户记忆档案

**参数：**
- `memory_types` (可选): 要获取的记忆类型

**示例：**
```json
{
  "name": "memory_get_profile",
  "arguments": {
    "memory_types": ["core", "semantic"]
  }
}
```

## 📊 可用资源

### 1. mirix://status
获取 MIRIX 后端状态信息

### 2. mirix://memory/stats
获取记忆系统统计信息

## 🐛 故障排除

### 常见问题

#### 1. 连接失败
**现象：** MCP 服务器无法连接到 MIRIX 后端

**解决方案：**
```bash
# 检查 MIRIX 后端是否运行
curl http://10.157.152.40:47283/health

# 检查配置
echo $MIRIX_BACKEND_URL

# 重新启动 MIRIX 后端
cd /opt/MIRIX
python3 main.py
```

#### 2. 工具调用失败
**现象：** 工具调用返回错误

**解决方案：**
```bash
# 启用调试模式
python3 run_mcp_server.py --debug

# 检查参数格式
# 确保 memory_type 是有效值
# 确认所有必需参数都已提供
```

#### 3. 兼容性问题
**现象：** 无法导入 MCP SDK

**解决方案：**
```bash
# 强制使用兼容版本
python3 run_mcp_server.py --force-compatible

# 或安装 MCP SDK（可选）
pip install mcp
```

### 调试技巧

#### 1. 查看详细日志
```bash
# 启用调试模式
python3 run_mcp_server.py --debug
```

#### 2. 测试单个组件
```bash
# 测试配置加载
python3 -c "from config_simple import get_settings; print(get_settings().mirix_backend_url)"

# 测试 MIRIX 客户端
python3 -c "
import asyncio
from mirix_client_simple import MIRIXClient
async def test():
    client = MIRIXClient('http://10.157.152.40:47283')
    await client.initialize()
    print(await client.health_check())
    await client.close()
asyncio.run(test())
"
```

#### 3. 运行完整测试
```bash
python3 test_mcp_server.py
```

### 性能优化

#### 1. 调整超时设置
```bash
export MIRIX_BACKEND_TIMEOUT=60  # 增加到 60 秒
```

#### 2. 限制搜索结果
```bash
export MEMORY_SEARCH_LIMIT=5     # 限制搜索结果数量
```

## 🔄 升级指南

### 从旧版本升级

1. **备份配置**
```bash
cp .env .env.backup
```

2. **更新代码**
```bash
# 重构的文件已经替换了旧版本
# 新文件列表：
# - server_compatible.py （兼容版本）
# - config_simple.py （简化配置）
# - mirix_client_simple.py （简化客户端）
# - run_mcp_server.py （统一启动脚本）
```

3. **测试新版本**
```bash
python3 run_mcp_server.py --test
```

4. **更新 Claude Desktop 配置**
```json
{
  "mcpServers": {
    "mirix-memory": {
      "command": "python3",
      "args": ["/opt/MIRIX/mcp_sse_service/run_mcp_server.py"],
      "cwd": "/opt/MIRIX/mcp_sse_service"
    }
  }
}
```

## 📚 API 参考

### JSON-RPC 接口

MCP 服务器支持标准的 JSON-RPC 2.0 协议：

#### 初始化
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "claude-desktop",
      "version": "1.0.0"
    }
  }
}
```

#### 列出工具
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

#### 调用工具
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "memory_add",
    "arguments": {
      "content": "记忆内容",
      "memory_type": "core"
    }
  }
}
```

## 🤝 支持

如果您遇到问题：

1. 首先运行测试套件诊断问题
2. 查看本文档的故障排除部分
3. 检查 MIRIX 后端日志
4. 在项目仓库提交 issue

---

**重构完成！** 🎉

新的 MCP 服务器具有以下优势：
- ✅ 简化的架构和配置
- ✅ 更好的错误处理和日志
- ✅ 兼容性版本支持
- ✅ 完整的测试套件
- ✅ 详细的文档和故障排除指南