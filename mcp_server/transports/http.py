"""
MIRIX MCP Server - HTTP 传输实现

该模块实现基于 HTTP 的 MCP 传输协议。
提供 RESTful API 接口和 JSON-RPC over HTTP 的功能。

主要功能：
1. HTTP 服务器实现
2. JSON-RPC over HTTP 支持
3. CORS 跨域支持
4. 请求验证和错误处理
5. 异步请求处理

作者：MIRIX MCP Server Team
版本：1.0.0
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from ..exceptions import TransportError, ValidationError
from ..utils import performance_monitor

# 配置日志
logger = logging.getLogger(__name__)


class HttpTransport:
    """
    HTTP 传输实现
    
    提供基于 HTTP 的 MCP 传输功能。
    支持 RESTful API 和 JSON-RPC over HTTP。
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        """
        初始化 HTTP 传输
        
        Args:
            host: 服务器主机地址
            port: 服务器端口
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI 未安装，无法使用 HTTP 传输")
        
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="MIRIX MCP Server",
            description="MIRIX Memory Management MCP Server HTTP API",
            version="1.0.0"
        )
        self.message_handler: Optional[Callable] = None
        self._server: Optional[uvicorn.Server] = None
        
        # 配置 CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 设置路由
        self._setup_routes()
        
        logger.info(f"HTTP 传输初始化完成 - {host}:{port}")
    
    def _setup_routes(self) -> None:
        """设置 HTTP 路由"""
        
        @self.app.get("/")
        async def root():
            """根路径 - 服务器信息"""
            return {
                "name": "MIRIX MCP Server",
                "version": "1.0.0",
                "transport": "HTTP",
                "status": "running"
            }
        
        @self.app.get("/health")
        async def health_check():
            """健康检查端点"""
            return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}
        
        @self.app.post("/mcp")
        async def mcp_endpoint(request: Request):
            """MCP JSON-RPC 端点"""
            try:
                # 读取请求体
                body = await request.body()
                if not body:
                    raise HTTPException(status_code=400, detail="请求体为空")
                
                # 解析 JSON
                try:
                    message = json.loads(body.decode('utf-8'))
                except json.JSONDecodeError as e:
                    raise HTTPException(status_code=400, detail=f"JSON 解析失败: {e}")
                
                # 处理消息
                if not self.message_handler:
                    raise HTTPException(status_code=500, detail="消息处理器未设置")
                
                response = await self.message_handler(message)
                
                return JSONResponse(content=response or {})
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"MCP 请求处理失败: {e}")
                raise HTTPException(status_code=500, detail=f"内部服务器错误: {e}")
        
        @self.app.post("/tools/{tool_name}")
        async def tool_endpoint(tool_name: str, request: Request):
            """工具调用端点"""
            try:
                # 读取请求体
                body = await request.body()
                arguments = {}
                
                if body:
                    try:
                        arguments = json.loads(body.decode('utf-8'))
                    except json.JSONDecodeError as e:
                        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {e}")
                
                # 构造 MCP 工具调用消息
                message = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                
                # 处理消息
                if not self.message_handler:
                    raise HTTPException(status_code=500, detail="消息处理器未设置")
                
                response = await self.message_handler(message)
                
                # 提取工具调用结果
                if response and "result" in response:
                    return JSONResponse(content=response["result"])
                else:
                    return JSONResponse(content=response or {})
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"工具调用失败: {e}")
                raise HTTPException(status_code=500, detail=f"工具调用失败: {e}")
        
        @self.app.get("/tools")
        async def list_tools():
            """列出可用工具"""
            try:
                # 构造 MCP 工具列表消息
                message = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list"
                }
                
                # 处理消息
                if not self.message_handler:
                    raise HTTPException(status_code=500, detail="消息处理器未设置")
                
                response = await self.message_handler(message)
                
                # 提取工具列表
                if response and "result" in response:
                    return JSONResponse(content=response["result"])
                else:
                    return JSONResponse(content={"tools": []})
                
            except Exception as e:
                logger.error(f"获取工具列表失败: {e}")
                raise HTTPException(status_code=500, detail=f"获取工具列表失败: {e}")
    
    def set_message_handler(self, handler: Callable) -> None:
        """
        设置消息处理器
        
        Args:
            handler: 消息处理器函数
        """
        self.message_handler = handler
        logger.info("HTTP 传输消息处理器已设置")
    
    @performance_monitor
    async def start_server(self) -> None:
        """
        启动 HTTP 服务器
        
        Raises:
            TransportError: 服务器启动失败
        """
        try:
            config = uvicorn.Config(
                app=self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
            
            self._server = uvicorn.Server(config)
            logger.info(f"启动 HTTP 服务器 - http://{self.host}:{self.port}")
            
            await self._server.serve()
            
        except Exception as e:
            logger.error(f"HTTP 服务器启动失败: {e}")
            raise TransportError(f"服务器启动失败: {e}")
    
    async def stop_server(self) -> None:
        """停止 HTTP 服务器"""
        if self._server:
            logger.info("停止 HTTP 服务器...")
            self._server.should_exit = True
            await self._server.shutdown()
            self._server = None
    
    @property
    def is_running(self) -> bool:
        """检查服务器是否在运行"""
        return self._server is not None and not self._server.should_exit


class HttpServer:
    """
    基于 HTTP 的 MCP 服务器
    
    使用 HTTP 传输实现完整的 MCP 服务器功能。
    """
    
    def __init__(self, message_handler, host: str = "127.0.0.1", port: int = 8000):
        """
        初始化 HTTP 服务器
        
        Args:
            message_handler: 消息处理器函数
            host: 服务器主机地址
            port: 服务器端口
        """
        self.transport = HttpTransport(host, port)
        self.transport.set_message_handler(message_handler)
        
        logger.info(f"HTTP 服务器初始化完成 - {host}:{port}")
    
    async def start(self) -> None:
        """
        启动服务器
        
        开始监听和处理 HTTP 请求。
        
        Raises:
            TransportError: 服务器启动失败
        """
        await self.transport.start_server()
    
    async def stop(self) -> None:
        """停止服务器"""
        await self.transport.stop_server()
    
    @property
    def is_running(self) -> bool:
        """检查服务器是否在运行"""
        return self.transport.is_running


# 便捷函数
async def run_http_server(message_handler, host: str = "127.0.0.1", port: int = 8000) -> None:
    """
    运行 HTTP 服务器的便捷函数
    
    Args:
        message_handler: 消息处理器函数
        host: 服务器主机地址
        port: 服务器端口
    """
    server = HttpServer(message_handler, host, port)
    await server.start()


@asynccontextmanager
async def http_transport(host: str = "127.0.0.1", port: int = 8000):
    """HTTP 传输的上下文管理器"""
    transport = HttpTransport(host, port)
    try:
        yield transport
    finally:
        await transport.stop_server()


# 工具函数
def create_error_response(request_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    """
    创建错误响应
    
    Args:
        request_id: 请求 ID
        code: 错误代码
        message: 错误消息
        data: 错误数据
        
    Returns:
        Dict[str, Any]: 错误响应
    """
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message
        }
    }
    
    if data is not None:
        response["error"]["data"] = data
    
    return response


def create_success_response(request_id: Any, result: Any) -> Dict[str, Any]:
    """
    创建成功响应
    
    Args:
        request_id: 请求 ID
        result: 结果数据
        
    Returns:
        Dict[str, Any]: 成功响应
    """
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }