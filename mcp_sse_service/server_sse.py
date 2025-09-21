#!/usr/bin/env python3
"""
MIRIX MCP 服务器 - SSE 版本

支持通过 Server-Sent Events (SSE) 提供记忆管理功能，
可以通过 HTTP 接口和 WebSocket 接口使用。
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config_simple import MCPServerSettings
from mirix_client_simple import MIRIXClient
from server_compatible import MCPServer

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPSSEServer:
    """支持 SSE 的 MCP 服务器"""

    def __init__(self, settings: MCPServerSettings):
        self.settings = settings
        self.mcp_server = MCPServer()

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # 启动
            success = await self.mcp_server.initialize()
            if not success:
                logger.error("Failed to initialize MCP server")
                raise RuntimeError("MCP server initialization failed")
            logger.info("MCP SSE Server started successfully")
            yield
            # 关闭
            await self.mcp_server.cleanup()
            logger.info("MCP SSE Server stopped")

        self.app = FastAPI(
            title="MIRIX MCP SSE Server",
            description="MIRIX Memory Agent MCP Server with SSE support",
            version="1.0.0",
            lifespan=lifespan
        )

        # 添加 CORS 支持
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_routes()

    def _setup_routes(self):
        """设置路由"""

        @self.app.get("/")
        async def root():
            """根路径"""
            return {
                "name": "MIRIX MCP SSE Server",
                "version": "1.0.0",
                "description": "MIRIX Memory Agent MCP Server with SSE support",
                "backend_url": self.settings.mirix_backend_url,
                "default_user_id": self.settings.default_user_id
            }

        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}

        @self.app.post("/mcp/request")
        async def handle_mcp_request(request: Request):
            """处理 MCP 请求"""
            try:
                data = await request.json()
                response = await self.mcp_server.handle_request(data)
                return response
            except Exception as e:
                logger.error(f"Error handling MCP request: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": data.get("id") if 'data' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }

        @self.app.get("/mcp/sse")
        async def mcp_sse_endpoint(request: Request):
            """SSE 端点"""
            async def event_stream():
                try:
                    # 发送初始连接确认
                    yield "data: " + json.dumps({
                        "type": "connection",
                        "status": "connected",
                        "timestamp": asyncio.get_event_loop().time()
                    }) + "\n\n"

                    # 保持连接活跃
                    while True:
                        # 定期发送心跳
                        yield "data: " + json.dumps({
                            "type": "heartbeat",
                            "timestamp": asyncio.get_event_loop().time()
                        }) + "\n\n"
                        await asyncio.sleep(30)  # 每30秒发送一次心跳

                except asyncio.CancelledError:
                    logger.info("SSE connection cancelled")
                except Exception as e:
                    logger.error(f"SSE stream error: {e}")
                    yield "data: " + json.dumps({
                        "type": "error",
                        "message": str(e)
                    }) + "\n\n"

            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control"
                }
            )

        # MCP 工具端点
        @self.app.post("/tools/memory_add")
        async def memory_add_endpoint(request: Request):
            """记忆添加端点"""
            try:
                data = await request.json()
                result = await self.mcp_server.memory_add(**data)
                return result
            except Exception as e:
                logger.error(f"Memory add error: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/tools/memory_search")
        async def memory_search_endpoint(request: Request):
            """记忆搜索端点"""
            try:
                data = await request.json()
                result = await self.mcp_server.memory_search(**data)
                return result
            except Exception as e:
                logger.error(f"Memory search error: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/tools/memory_chat")
        async def memory_chat_endpoint(request: Request):
            """记忆聊天端点"""
            try:
                data = await request.json()
                result = await self.mcp_server.memory_chat(**data)
                return result
            except Exception as e:
                logger.error(f"Memory chat error: {e}")
                return {"success": False, "error": str(e)}

        @self.app.get("/tools/memory_get_profile")
        async def memory_get_profile_endpoint():
            """获取用户记忆档案端点"""
            try:
                result = await self.mcp_server.memory_get_profile()
                return result
            except Exception as e:
                logger.error(f"Get profile error: {e}")
                return {"success": False, "error": str(e)}

        # 资源端点
        @self.app.get("/resources/status")
        async def status_resource():
            """状态资源"""
            content = await self.mcp_server.get_mirix_status()
            return json.loads(content)

        @self.app.get("/resources/memory_stats")
        async def memory_stats_resource():
            """记忆统计资源"""
            content = await self.mcp_server.get_memory_stats()
            return json.loads(content)

    async def start(self):
        """启动服务器"""
        config = uvicorn.Config(
            self.app,
            host=self.settings.sse_host,
            port=self.settings.sse_port,
            log_level="info" if not self.settings.debug else "debug",
            access_log=True
        )
        server = uvicorn.Server(config)

        logger.info(f"Starting MIRIX MCP SSE Server on {self.settings.sse_host}:{self.settings.sse_port}")
        await server.serve()


async def main(settings: MCPServerSettings):
    """主函数"""
    logger.info("Starting MIRIX MCP Server (SSE Version)")
    logger.info(f"MIRIX Backend URL: {settings.mirix_backend_url}")
    logger.info(f"Default User ID: {settings.default_user_id}")
    logger.info(f"SSE Server: {settings.sse_host}:{settings.sse_port}")

    try:
        sse_server = MCPSSEServer(settings)
        await sse_server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from config_simple import get_settings

    settings = get_settings()
    settings.sse_enabled = True
    settings.sse_host = "localhost"
    settings.sse_port = 8080

    asyncio.run(main(settings))