# MIRIX MCP 服务安装和配置指南

## 系统要求

### 最低要求
- **操作系统**: Linux, macOS, Windows 10+
- **Python**: 3.8 或更高版本
- **内存**: 最少 2GB RAM
- **存储**: 最少 1GB 可用空间
- **网络**: 能够访问 MIRIX 后端服务

### 推荐配置
- **操作系统**: Ubuntu 20.04+ / macOS 12+ / Windows 11
- **Python**: 3.10 或更高版本
- **内存**: 4GB+ RAM
- **存储**: 5GB+ 可用空间
- **网络**: 稳定的网络连接

## 安装步骤

### 1. 环境准备

#### 检查 Python 版本
```bash
python --version
# 或
python3 --version
```

如果 Python 版本低于 3.8，请先升级 Python。

#### 创建虚拟环境（推荐）
```bash
# 创建虚拟环境
python -m venv mirix_mcp_env

# 激活虚拟环境
# Linux/macOS:
source mirix_mcp_env/bin/activate

# Windows:
mirix_mcp_env\Scripts\activate
```

### 2. 获取源码

#### 方式一：从 Git 仓库克隆
```bash
git clone https://github.com/Mirix-AI/MIRIX.git
cd MIRIX
```

#### 方式二：下载源码包
```bash
# 下载并解压源码包
wget https://github.com/Mirix-AI/MIRIX/archive/main.zip
unzip main.zip
cd MIRIX-main
```

### 3. 安装依赖

#### 安装 Python 依赖
```bash
# 安装基础依赖
pip install -r requirements.txt

# 如果需要开发依赖
pip install -r requirements-dev.txt
```

#### 核心依赖说明
```txt
# MCP 协议支持
mcp>=1.0.0

# 异步 HTTP 客户端
aiohttp>=3.8.0
httpx>=0.24.0

# 配置管理
pydantic>=2.0.0
pydantic-settings>=2.0.0

# 日志和工具
structlog>=23.0.0
python-dotenv>=1.0.0
```

### 4. 配置设置

#### 创建配置文件

在项目根目录创建 `.env` 文件：

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

#### 基础配置示例

```bash
# ===========================================
# MIRIX MCP 服务器配置
# ===========================================

# 服务器基本信息
MCP_SERVER_NAME="MIRIX MCP Server"
MCP_SERVER_VERSION="1.0.0"

# 传输配置
MCP_TRANSPORT_TYPE="stdio"  # stdio 或 sse

# SSE 传输配置（仅在 transport_type="sse" 时使用）
MCP_SSE_HOST="0.0.0.0"
MCP_SSE_PORT=18002
MCP_SSE_HEARTBEAT_INTERVAL=30

# MIRIX 后端集成配置
MIRIX_BACKEND_URL="http://10.157.152.40:47283"
MIRIX_BACKEND_TIMEOUT=30

# 记忆管理配置
MCP_DEFAULT_USER_ID="default_user"
MCP_MEMORY_SEARCH_LIMIT=10

# 日志配置
MCP_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
MCP_DEBUG=false

# MCP 协议配置
MCP_VERSION="2024-11-05"
```

#### 高级配置选项

```bash
# ===========================================
# 高级配置选项
# ===========================================

# 性能调优
MCP_MAX_CONCURRENT_REQUESTS=10
MCP_REQUEST_TIMEOUT=60
MCP_CONNECTION_POOL_SIZE=20

# 安全配置
MCP_ENABLE_CORS=true
MCP_ALLOWED_ORIGINS="*"
MCP_API_KEY_REQUIRED=false

# 缓存配置
MCP_ENABLE_CACHE=true
MCP_CACHE_TTL=3600
MCP_CACHE_MAX_SIZE=1000

# 监控配置
MCP_ENABLE_METRICS=true
MCP_METRICS_PORT=9090
MCP_HEALTH_CHECK_INTERVAL=30
```

### 5. 验证安装

#### 运行基础测试
```bash
# 检查配置
python -m mcp_server.config --check

# 运行健康检查
python -m mcp_server.server --health-check

# 启动服务器（测试模式）
python -m mcp_server.server --test
```

#### 验证工具注册
```bash
# 列出所有可用工具
python -c "
from mcp_server.tools import get_tool_names
print('可用工具:', get_tool_names())
"
```

预期输出：
```
可用工具: ['memory_add', 'memory_search', 'memory_chat', 'memory_get_profile']
```

## 客户端集成配置

### Claude Desktop 配置

#### 1. 找到配置文件位置
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

#### 2. 添加 MCP 服务器配置
```json
{
  "mcpServers": {
    "mirix-memory": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/MIRIX",
      "env": {
        "MIRIX_BACKEND_URL": "http://10.157.152.40:47283",
        "MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### 3. 重启 Claude Desktop
重启 Claude Desktop 应用程序以加载新的 MCP 服务器配置。

### Cline (VS Code) 配置

#### 1. 打开 Cline 设置
在 VS Code 中打开 Cline 扩展设置。

#### 2. 添加 MCP 服务器
```json
{
  "cline.mcpServers": [
    {
      "name": "MIRIX Memory",
      "command": ["python", "-m", "mcp_server.server"],
      "cwd": "/path/to/MIRIX",
      "env": {
        "MIRIX_BACKEND_URL": "http://10.157.152.40:47283"
      }
    }
  ]
}
```

### 其他 MCP 客户端

对于其他支持 MCP 协议的客户端，通常需要配置：

- **命令**: `python -m mcp_server.server`
- **工作目录**: MIRIX 项目根目录
- **环境变量**: 根据需要设置配置参数

## 服务启动方式

### 1. 直接启动（stdio 模式）

```bash
# 基本启动
python -m mcp_server.server

# 指定配置文件
python -m mcp_server.server --config /path/to/config.env

# 调试模式
python -m mcp_server.server --debug
```

### 2. SSE 模式启动

```bash
# 启动 SSE 服务器
python -m mcp_server.server --transport sse

# 指定端口
python -m mcp_server.server --transport sse --port 18002

# 指定主机和端口
python -m mcp_server.server --transport sse --host 0.0.0.0 --port 18002
```

### 3. 作为系统服务

#### 创建 systemd 服务文件（Linux）

```bash
sudo nano /etc/systemd/system/mirix-mcp.service
```

```ini
[Unit]
Description=MIRIX MCP Server
After=network.target

[Service]
Type=simple
User=mirix
WorkingDirectory=/opt/MIRIX
Environment=PATH=/opt/MIRIX/mirix_mcp_env/bin
ExecStart=/opt/MIRIX/mirix_mcp_env/bin/python -m mcp_server.server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable mirix-mcp
sudo systemctl start mirix-mcp
sudo systemctl status mirix-mcp
```

### 4. Docker 部署

#### 创建 Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY . .

# 暴露端口（SSE 模式）
EXPOSE 18002

# 启动命令
CMD ["python", "-m", "mcp_server.server"]
```

#### 构建和运行
```bash
# 构建镜像
docker build -t mirix-mcp .

# 运行容器（stdio 模式）
docker run -it mirix-mcp

# 运行容器（SSE 模式）
docker run -p 18002:18002 -e MCP_TRANSPORT_TYPE=sse mirix-mcp
```

## 配置验证

### 1. 检查配置文件
```bash
python -c "
from mcp_server.config import get_config
config = get_config()
print(f'服务器名称: {config.server_name}')
print(f'传输类型: {config.transport_type}')
print(f'后端 URL: {config.mirix_backend_url}')
print(f'日志级别: {config.log_level}')
"
```

### 2. 测试后端连接
```bash
python -c "
import asyncio
from mcp_server.mirix_adapter import MIRIXAdapter
from mcp_server.config import get_config

async def test_connection():
    config = get_config()
    adapter = MIRIXAdapter(config)
    try:
        result = await adapter.health_check()
        print('后端连接成功:', result)
    except Exception as e:
        print('后端连接失败:', e)

asyncio.run(test_connection())
"
```

### 3. 验证工具功能
```bash
python -c "
import asyncio
from mcp_server.tools import initialize_tools, execute_tool

async def test_tools():
    initialize_tools()
    
    # 测试记忆添加
    result = await execute_tool('memory_add', {
        'content': '这是一个测试记忆',
        'memory_type': 'core'
    })
    print('记忆添加测试:', result['success'])
    
    # 测试记忆搜索
    result = await execute_tool('memory_search', {
        'query': '测试'
    })
    print('记忆搜索测试:', result['success'])

asyncio.run(test_tools())
"
```

## 常见安装问题

### 1. Python 版本问题
```bash
# 错误：Python 版本过低
# 解决：升级 Python 或使用 pyenv
pyenv install 3.10.0
pyenv local 3.10.0
```

### 2. 依赖安装失败
```bash
# 错误：pip 安装失败
# 解决：升级 pip 和 setuptools
pip install --upgrade pip setuptools wheel

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 3. 权限问题
```bash
# 错误：权限不足
# 解决：使用虚拟环境或用户安装
pip install --user -r requirements.txt
```

### 4. 网络连接问题
```bash
# 错误：无法连接到 MIRIX 后端
# 解决：检查网络配置和防火墙设置
curl -v http://10.157.152.40:47283/health

# 配置代理（如果需要）
export HTTP_PROXY=http://proxy.example.com:18002
export HTTPS_PROXY=http://proxy.example.com:18002
```

## 下一步

安装完成后，您可以：

1. 查看 [API 参考文档](./API_REFERENCE.md) 了解详细的 API 使用方法
2. 参考 [使用示例](./USAGE_EXAMPLES.md) 学习实际应用场景
3. 阅读 [故障排除指南](./TROUBLESHOOTING.md) 解决可能遇到的问题

---

**版本**: 1.0.0  
**更新时间**: 2024-01-01  
**维护团队**: MIRIX MCP Server Team