"""
MCP Server 模块

这是一个基于官方 MCP Python SDK 的服务器实现，用于替代原有的 mcp_sse_service。
主要功能包括：
- 记忆管理工具（添加、搜索、对话、档案查询）
- 支持 stdio 和 SSE 传输方式
- 与 MIRIX 后端系统集成

主要组件：
- server.py: MCP 服务器核心实现
- config.py: 配置管理
- mirix_adapter.py: MIRIX 客户端适配器
- tools/: 记忆管理工具模块
- transports/: 传输层实现
"""

__version__ = "1.0.0"
__author__ = "MIRIX Team"

# 导出主要组件
from .server import MCPServer
from .config import MCPServerConfig

__all__ = ["MCPServer", "MCPServerConfig"]