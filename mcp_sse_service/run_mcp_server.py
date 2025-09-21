#!/usr/bin/env python3
"""
MIRIX MCP 服务器启动脚本

支持官方 MCP SDK 和兼容版本的自动切换。
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config_simple import get_settings


def setup_logging(debug: bool = False):
    """设置日志配置"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)  # 输出到 stderr，避免与 MCP 通信冲突
        ]
    )


def check_mcp_sdk():
    """检查 MCP SDK 是否可用"""
    try:
        from mcp.server.fastmcp import FastMCP
        return True
    except ImportError:
        return False


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MIRIX MCP 服务器")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--test", action="store_true", help="运行测试模式")
    parser.add_argument("--force-compatible", action="store_true", help="强制使用兼容版本")

    # 新增配置选项
    parser.add_argument("--backend-url", type=str, help="MIRIX 后端服务 URL")
    parser.add_argument("--user-id", type=str, help="默认用户 ID")
    parser.add_argument("--sse-port", type=int, help="SSE 服务器端口（如果启用 SSE）")
    parser.add_argument("--sse-host", type=str, help="SSE 服务器主机地址")
    parser.add_argument("--enable-sse", action="store_true", help="启用 SSE 服务器模式")

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)

    # 加载设置 - 支持命令行参数覆盖
    settings = get_settings(
        custom_backend_url=args.backend_url,
        custom_user_id=args.user_id
    )

    # 应用命令行参数
    if args.sse_port:
        settings.sse_port = args.sse_port
    if args.sse_host:
        settings.sse_host = args.sse_host
    if args.enable_sse:
        settings.sse_enabled = True

    # 打印配置信息
    logger.info(f"MIRIX Backend URL: {settings.mirix_backend_url}")
    logger.info(f"Default User ID: {settings.default_user_id}")
    if settings.sse_enabled:
        logger.info(f"SSE Server: {settings.sse_host}:{settings.sse_port}")

    if args.test:
        # 测试模式
        logger.info("启动测试模式...")
        from test_mcp_server import main as run_tests
        success = await run_tests()
        sys.exit(0 if success else 1)
    else:
        # TODO(human): 在这里添加任何自定义的启动验证或配置
        # 例如：特殊的环境检查、用户认证、自定义端口等

        # 检查 MCP SDK 可用性
        has_mcp_sdk = check_mcp_sdk() and not args.force_compatible

        if has_mcp_sdk:
            logger.info("使用官方 MCP SDK 版本...")
            try:
                from server import main as run_mcp_server
                await run_mcp_server()
            except Exception as e:
                logger.error(f"官方版本启动失败，切换到兼容版本: {e}")
                has_mcp_sdk = False

        if not has_mcp_sdk:
            logger.info("使用兼容版本（不依赖 MCP SDK）...")

            try:
                # 根据配置选择运行模式
                if settings.sse_enabled:
                    logger.info("启动 SSE 服务器模式...")
                    from server_sse import main as run_sse_server
                    await run_sse_server(settings)
                else:
                    logger.info("启动标准 stdio 模式...")
                    from server_compatible import main as run_compatible_server
                    await run_compatible_server()
            except KeyboardInterrupt:
                logger.info("服务器停止")
            except Exception as e:
                logger.error(f"服务器启动失败: {e}")
                sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())