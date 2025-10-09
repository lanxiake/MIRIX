#!/usr/bin/env python3
"""
本地启动 MCP 服务器脚本

直接使用 Python 启动 MCP 服务器，不依赖 Docker
适用于开发和测试环境
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置环境变量（如果需要的话）
os.environ.setdefault('MIRIX_BACKEND_URL', 'http://localhost:47283')
os.environ.setdefault('MCP_SSE_HOST', '0.0.0.0')  
os.environ.setdefault('MCP_SSE_PORT', '18002')
os.environ.setdefault('MCP_LOG_LEVEL', 'INFO')
os.environ.setdefault('MCP_DEBUG', 'true')

def check_dependencies():
    """检查必要的依赖是否已安装"""
    try:
        import mcp
        import fastapi
        import uvicorn
        import httpx
        import pydantic_settings
        print("✅ 所有必要的依赖都已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少必要的依赖: {e}")
        print("请安装缺少的依赖:")
        print("pip install mcp fastapi uvicorn httpx pydantic-settings")
        return False

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('mcp_server.log')
        ]
    )

async def start_server():
    """启动 MCP 服务器"""
    try:
        from mcp_server.config import get_config
        from mcp_server.server import MCPServer
        
        # 获取配置
        config = get_config()
        print(f"📋 加载配置:")
        print(f"  - 服务名称: {config.server_name}")
        print(f"  - 服务版本: {config.server_version}")
        print(f"  - 监听地址: {config.sse_host}:{config.sse_port}")
        print(f"  - MIRIX 后端: {config.mirix_backend_url}")
        
        # 创建服务器实例
        server = MCPServer(config)
        
        print("🚀 正在启动 MCP 服务器...")
        print(f"📡 服务端点: http://{config.sse_host}:{config.sse_port}{config.sse_endpoint}")
        
        # 启动服务器
        await server.run_sse()
        
    except KeyboardInterrupt:
        print("\n⏹️  服务器已停止")
    except Exception as e:
        print(f"❌ 启动服务器时出错: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🔧 MIRIX MCP 服务器本地启动工具")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 设置日志
    setup_logging()
    
    # 启动服务器
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\n👋 再见！")
        return 0
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
