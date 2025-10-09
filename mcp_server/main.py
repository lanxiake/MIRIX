"""
MCP Server 主程序入口 - 纯SSE模式

提供基于SSE (Server-Sent Events) 的MCP服务器实现。
支持命令行参数配置和优雅关闭机制。

使用方式：
    # 使用默认配置启动
    python -m mcp_server
    
    # 指定端口和主机
    python -m mcp_server --port 18002 --host 0.0.0.0
    
    # 指定配置文件
    python -m mcp_server --config /path/to/config.yaml
    
    # 启用调试模式
    python -m mcp_server --debug

作者：MIRIX MCP Server Team
版本：2.0.0 (SSE Only)
"""

import argparse
import sys
import os
import asyncio
import signal
import logging
from pathlib import Path
from typing import Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.config import get_config, MCPServerConfig
from mcp_server.server import MCPServer


# 全局服务器实例，用于优雅关闭
_server_instance: Optional[MCPServer] = None


def setup_logging(config: MCPServerConfig) -> None:
    """设置日志配置
    
    Args:
        config: 服务器配置
    """
    # SSE模式使用标准输出进行日志记录
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 设置第三方库日志级别
    if not config.debug:
        logging.getLogger("aiohttp").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)


def setup_signal_handlers() -> None:
    """设置信号处理器，用于优雅关闭"""
    def signal_handler(signum, frame):
        """信号处理函数"""
        logger = logging.getLogger(__name__)
        logger.info(f"收到信号 {signum}，正在关闭服务器...")
        
        # 如果有运行中的服务器实例，尝试优雅关闭
        if _server_instance:
            asyncio.create_task(_server_instance.shutdown())
        
        # 设置退出标志
        sys.exit(0)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def run_sse_server(config: MCPServerConfig) -> None:
    """运行 SSE 传输模式的服务器
    
    Args:
        config: 服务器配置
    """
    global _server_instance
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("启动 MIRIX MCP 服务器 - SSE 模式")
    logger.info("=" * 50)
    logger.info(f"服务器名称: {config.server_name}")
    logger.info(f"服务器版本: {config.server_version}")
    logger.info(f"监听地址: {config.sse_host}:{config.sse_port}")
    logger.info(f"MIRIX 后端: {config.mirix_backend_url}")
    logger.info(f"调试模式: {'启用' if config.debug else '禁用'}")
    logger.info(f"服务端点: http://{config.sse_host}:{config.sse_port}/sse")
    logger.info("=" * 50)
    
    try:
        # 创建并运行服务器
        _server_instance = MCPServer(config)
        await _server_instance.run_sse()
    except Exception as e:
        logger.error(f"SSE 服务器运行失败: {e}")
        raise
    finally:
        _server_instance = None


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description="MIRIX MCP Server - 基于SSE的记忆管理服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s                           # 使用默认配置启动
  %(prog)s --port 18002               # 指定端口
  %(prog)s --host 0.0.0.0            # 指定监听地址
  %(prog)s --config config.yaml     # 使用指定配置文件
  %(prog)s --debug                   # 启用调试模式
  %(prog)s --help                    # 显示帮助信息
        """
    )
    
    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="配置文件路径"
    )
    
    parser.add_argument(
        "--host",
        help="SSE服务器监听主机 (默认: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        help="SSE服务器监听端口 (默认: 18002)"
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="启用调试模式"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别 (默认: INFO)"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="MIRIX MCP Server 2.0.0 (SSE Only)"
    )
    
    return parser.parse_args()


async def main() -> None:
    """主程序入口
    
    启动SSE模式的MCP服务器。
    """
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 加载配置
        config = get_config(config_path=args.config)
        
        # 强制设置为SSE模式
        config.transport_type = "sse"
        
        # 应用命令行参数覆盖
        if args.host:
            config.sse_host = args.host
        if args.port:
            config.sse_port = args.port
        if args.debug:
            config.debug = True
        if args.log_level:
            config.log_level = args.log_level
        
        # 设置日志
        setup_logging(config)
        
        # 设置信号处理器
        setup_signal_handlers()
        
        logger = logging.getLogger(__name__)
        logger.info("MIRIX MCP Server 正在启动...")
        
        # 启动SSE服务器
        await run_sse_server(config)
            
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logging.getLogger(__name__).error(f"服务器启动失败: {e}")
        if "--debug" in sys.argv or "-d" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def cli_main() -> None:
    """命令行入口点
    
    用于 setup.py 或 pyproject.toml 中的 console_scripts。
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"启动失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()