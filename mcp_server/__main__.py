#!/usr/bin/env python3
"""
MIRIX MCP Server - 模块入口文件

该文件支持使用 python -m mcp_server 命令启动服务器。

使用方法：
    python -m mcp_server                    # 使用默认配置启动
    python -m mcp_server --help             # 显示帮助信息

作者：MIRIX MCP Server Team
版本：1.0.0
"""

from .main import cli_main

if __name__ == "__main__":
    cli_main()