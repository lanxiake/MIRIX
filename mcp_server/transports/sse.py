"""
MIRIX MCP Server - SSE 传输层

该模块实现基于 Server-Sent Events 的 MCP 传输层，
提供基于 HTTP 的实时双向通信能力。

主要功能：
1. SSE 服务器实现
2. HTTP 请求处理
3. 实时消息推送
4. 连接状态管理
5. 跨域支持

作者：MIRIX MCP Server Team
版本：1.0.0
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, Awaitable, Set
from contextlib import asynccontextmanager
from aiohttp import web, WSMsgType
from aiohttp.web_request import Request
from aiohttp.web_response import Response, StreamResponse

# MCP SDK 导入
try:
    from mcp.server.sse import SseServerTransport
    from mcp.server.lowlevel import Server
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from ..exceptions import TransportError, ValidationError
from ..utils import measure_time_async

# 配置日志
logger = logging.getLogger(__name__)


class SseTransport:
    """
    SSE 传输层实现
    
    提供基于 Server-Sent Events 的 MCP 传输功能，
    支持通过 HTTP 进行实时双向通信。
    """
    
    def __init__(self, host: str = "localhost", port: int = 18002):
        """
        初始化 SSE 传输层
        
        Args:
            host: 监听主机地址
            port: 监听端口
        """
        self.host = host
        self.port = port
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self._connected_clients: Set[StreamResponse] = set()
        self._message_handler: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None
        
        logger.info(f"SSE 传输层初始化完成，监听 {host}:{port}")
    
    def set_message_handler(self, handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]) -> None:
        """
        设置消息处理器
        
        Args:
            handler: 消息处理函数
        """
        self._message_handler = handler
        logger.info("消息处理器已设置")
    
    async def _setup_routes(self) -> None:
        """设置路由"""
        if not self.app:
            return
        
        # SSE 连接端点
        self.app.router.add_get('/sse', self._handle_sse_connection)
        
        # 消息发送端点
        self.app.router.add_post('/message', self._handle_message)
        
        # 健康检查端点
        self.app.router.add_get('/health', self._handle_health)
        
        # 静态文件服务 (可选)
        self.app.router.add_get('/', self._handle_index)
        
        logger.info("路由设置完成")
    
    async def _handle_sse_connection(self, request: Request) -> StreamResponse:
        """
        处理 SSE 连接
        
        Args:
            request: HTTP 请求
            
        Returns:
            StreamResponse: SSE 响应流
        """
        logger.info(f"新的 SSE 连接: {request.remote}")
        
        # 创建 SSE 响应
        response = StreamResponse(
            status=200,
            reason='OK',
            headers={
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
        
        await response.prepare(request)
        
        # 添加到连接列表
        self._connected_clients.add(response)
        
        try:
            # 发送连接确认
            await self._send_sse_message(response, {
                "type": "connection",
                "status": "connected",
                "timestamp": asyncio.get_event_loop().time()
            })
            
            # 保持连接
            while not response.transport.is_closing():
                await asyncio.sleep(1)
                
                # 发送心跳
                await self._send_sse_message(response, {
                    "type": "heartbeat",
                    "timestamp": asyncio.get_event_loop().time()
                })
                
        except Exception as e:
            logger.error(f"SSE 连接异常: {e}")
        finally:
            # 从连接列表移除
            self._connected_clients.discard(response)
            logger.info(f"SSE 连接已断开: {request.remote}")
        
        return response
    
    async def _handle_message(self, request: Request) -> Response:
        """
        处理消息请求
        
        Args:
            request: HTTP 请求
            
        Returns:
            Response: HTTP 响应
        """
        try:
            # 解析请求数据
            data = await request.json()
            logger.debug(f"接收消息: {data}")
            
            # 处理消息
            if self._message_handler:
                response_data = await self._message_handler(data)
                
                # 广播响应到所有连接的客户端
                await self._broadcast_message(response_data)
                
                return web.json_response({
                    "status": "success",
                    "message": "消息已处理"
                })
            else:
                return web.json_response({
                    "status": "error",
                    "message": "未设置消息处理器"
                }, status=500)
                
        except Exception as e:
            logger.error(f"消息处理失败: {e}")
            return web.json_response({
                "status": "error",
                "message": f"处理失败: {e}"
            }, status=500)
    
    async def _handle_health(self, request: Request) -> Response:
        """
        处理健康检查请求
        
        Args:
            request: HTTP 请求
            
        Returns:
            Response: 健康状态响应
        """
        return web.json_response({
            "status": "healthy",
            "transport": "sse",
            "connected_clients": len(self._connected_clients),
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def _handle_index(self, request: Request) -> Response:
        """
        处理首页请求
        
        Args:
            request: HTTP 请求
            
        Returns:
            Response: HTML 响应
        """
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>MIRIX MCP Server - SSE Transport</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>MIRIX MCP Server</h1>
            <h2>SSE Transport Layer</h2>
            <p>服务器正在运行，监听 SSE 连接。</p>
            <p>连接端点: <code>/sse</code></p>
            <p>消息端点: <code>/message</code></p>
            <p>健康检查: <code>/health</code></p>
        </body>
        </html>
        """
        
        return Response(
            text=html_content,
            content_type='text/html'
        )
    
    async def _send_sse_message(self, response: StreamResponse, data: Dict[str, Any]) -> None:
        """
        发送 SSE 消息
        
        Args:
            response: SSE 响应流
            data: 消息数据
        """
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            message = f"data: {json_data}\n\n"
            
            await response.write(message.encode('utf-8'))
            await response.drain()
            
        except Exception as e:
            logger.error(f"发送 SSE 消息失败: {e}")
    
    async def _broadcast_message(self, data: Dict[str, Any]) -> None:
        """
        广播消息到所有连接的客户端
        
        Args:
            data: 消息数据
        """
        if not self._connected_clients:
            logger.warning("没有连接的客户端，跳过广播")
            return
        
        logger.debug(f"广播消息到 {len(self._connected_clients)} 个客户端")
        
        # 复制客户端列表以避免并发修改
        clients = list(self._connected_clients)
        
        for client in clients:
            try:
                await self._send_sse_message(client, data)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                # 移除失效的连接
                self._connected_clients.discard(client)
    
    @asynccontextmanager
    async def connect(self):
        """
        建立 SSE 服务器连接
        
        Yields:
            SseTransport: 连接的传输实例
        """
        try:
            logger.info(f"启动 SSE 服务器，监听 {self.host}:{self.port}")
            
            # 创建应用
            self.app = web.Application()
            
            # 设置路由
            await self._setup_routes()
            
            # 创建运行器
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            # 创建站点
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            logger.info(f"SSE 服务器已启动: http://{self.host}:{self.port}")
            
            try:
                yield self
            finally:
                await self._disconnect()
                
        except Exception as e:
            logger.error(f"SSE 服务器启动失败: {e}")
            raise TransportError(f"服务器启动失败: {e}")
    
    async def _disconnect(self) -> None:
        """断开连接"""
        try:
            logger.info("关闭 SSE 服务器...")
            
            # 关闭所有客户端连接
            for client in list(self._connected_clients):
                try:
                    await client.write_eof()
                except Exception:
                    pass
            
            self._connected_clients.clear()
            
            # 关闭站点
            if self.site:
                await self.site.stop()
                self.site = None
            
            # 清理运行器
            if self.runner:
                await self.runner.cleanup()
                self.runner = None
            
            self.app = None
            
            logger.info("SSE 服务器已关闭")
            
        except Exception as e:
            logger.error(f"关闭 SSE 服务器失败: {e}")
    
    @property
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.site is not None and not self.site._server.is_serving()
    
    @property
    def connected_clients_count(self) -> int:
        """获取连接的客户端数量"""
        return len(self._connected_clients)
    
    async def run_with_server(self, server: 'Server') -> None:
        """
        与 MCP 服务器一起运行
        
        Args:
            server: MCP 服务器实例
        """
        if not MCP_AVAILABLE:
            raise TransportError("MCP SDK 不可用")
        
        try:
            logger.info("开始运行 MCP 服务器 (SSE 模式)...")
            
            # 使用 MCP SDK 的 SSE 传输
            transport = SseServerTransport(
                host=self.host,
                port=self.port
            )
            
            # 运行服务器
            async with transport as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    server.create_initialization_options()
                )
                
        except Exception as e:
            logger.error(f"服务器运行失败: {e}")
            raise TransportError(f"服务器运行失败: {e}")


# 便捷函数
@asynccontextmanager
async def create_sse_transport(host: str = "localhost", port: int = 18002):
    """
    创建 SSE 传输实例
    
    Args:
        host: 监听主机地址
        port: 监听端口
        
    Yields:
        SseTransport: 传输实例
    """
    transport = SseTransport(host, port)
    async with transport.connect():
        yield transport


async def run_sse_transport(
    message_handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
    host: str = "localhost",
    port: int = 18002
) -> None:
    """
    运行 SSE 传输
    
    Args:
        message_handler: 消息处理函数
        host: 监听主机地址
        port: 监听端口
    """
    async with create_sse_transport(host, port) as transport:
        transport.set_message_handler(message_handler)
        
        # 保持服务器运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到中断信号，关闭服务器")


if __name__ == "__main__":
    # 测试传输层
    async def test_handler(message: Dict[str, Any]) -> Dict[str, Any]:
        """测试消息处理器"""
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {"echo": message}
        }
    
    # 运行测试
    asyncio.run(run_sse_transport(test_handler))