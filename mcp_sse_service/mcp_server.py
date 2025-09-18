"""
MCP SSE Server 核心实现

实现MCP (Model Context Protocol) 协议的SSE (Server-Sent Events) 传输层。
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .config import Settings, get_settings
from .logging_config import LoggerMixin
from .mcp_protocol import MCPMessage, MCPRequest, MCPResponse, MCPNotification
from .mirix_client import MIRIXClient
from .session_manager import SessionManager
from .rate_limiter import RateLimiter

class MCPSSEServer(LoggerMixin):
    """MCP SSE服务器实现"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.router = APIRouter()
        self.mirix_client = MIRIXClient(settings.mirix_backend_url, settings.mirix_backend_timeout)
        self.session_manager = SessionManager(settings)
        self.rate_limiter = RateLimiter(settings.rate_limit_requests, settings.rate_limit_window)
        self._setup_routes()
        
        # 服务器状态
        self.server_info = {
            "name": "mirix-mcp-sse",
            "version": "0.1.0",
            "protocolVersion": settings.mcp_version,
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
                "logging": {}
            }
        }
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.router.get("/")
        async def mcp_root():
            """MCP服务根路径"""
            return {
                "service": "MIRIX MCP SSE Service",
                "protocol": "MCP",
                "transport": "SSE",
                "version": self.server_info["version"],
                "protocolVersion": self.server_info["protocolVersion"]
            }
        
        @self.router.post("/connect")
        async def connect_client(request: Request):
            """建立MCP连接"""
            client_ip = request.client.host
            
            # 速率限制检查
            if not await self.rate_limiter.allow_request(client_ip):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # 创建会话
            session_id = str(uuid.uuid4())
            session = await self.session_manager.create_session(session_id, client_ip)
            
            self.logger.info("New MCP client connected", session_id=session_id, client_ip=client_ip)
            
            return {
                "session_id": session_id,
                "server_info": self.server_info,
                "sse_endpoint": f"/mcp/sse/{session_id}"
            }
        
        @self.router.get("/sse/{session_id}")
        async def sse_stream(session_id: str, request: Request):
            """SSE流端点"""
            # 验证会话
            session = await self.session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # 更新会话活动时间
            await self.session_manager.update_session_activity(session_id)
            
            return StreamingResponse(
                self._sse_generator(session_id, request),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # 禁用nginx缓冲
                }
            )
        
        @self.router.post("/message/{session_id}")
        async def send_message(session_id: str, message: MCPMessage, request: Request):
            """发送MCP消息"""
            # 验证会话
            session = await self.session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # 速率限制检查
            client_ip = request.client.host
            if not await self.rate_limiter.allow_request(client_ip):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # 处理消息
            try:
                await self._handle_mcp_message(session_id, message)
                return {"status": "accepted"}
            except Exception as e:
                self.logger.error("Error handling MCP message", 
                                session_id=session_id, error=str(e))
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @self.router.delete("/disconnect/{session_id}")
        async def disconnect_client(session_id: str):
            """断开MCP连接"""
            await self.session_manager.remove_session(session_id)
            self.logger.info("MCP client disconnected", session_id=session_id)
            return {"status": "disconnected"}
    
    async def _sse_generator(self, session_id: str, request: Request) -> AsyncGenerator[str, None]:
        """SSE事件生成器"""
        try:
            # 发送连接确认
            yield self._format_sse_event("connected", {
                "session_id": session_id,
                "server_info": self.server_info
            })
            
            # 获取会话消息队列
            message_queue = await self.session_manager.get_message_queue(session_id)
            
            # 心跳任务
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(session_id, self.settings.sse_heartbeat_interval)
            )
            
            try:
                while True:
                    # 检查客户端是否断开连接
                    if await request.is_disconnected():
                        self.logger.info("Client disconnected", session_id=session_id)
                        break
                    
                    try:
                        # 等待消息或超时
                        message = await asyncio.wait_for(
                            message_queue.get(),
                            timeout=1.0
                        )
                        
                        # 发送消息
                        yield self._format_sse_event("message", message)
                        
                        # 标记任务完成
                        message_queue.task_done()
                        
                    except asyncio.TimeoutError:
                        # 超时，继续循环
                        continue
                    
            finally:
                # 清理
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
                
        except Exception as e:
            self.logger.error("SSE stream error", session_id=session_id, error=str(e))
            yield self._format_sse_event("error", {"error": str(e)})
        
        finally:
            # 清理会话
            await self.session_manager.remove_session(session_id)
    
    async def _heartbeat_loop(self, session_id: str, interval: int):
        """心跳循环"""
        while True:
            try:
                await asyncio.sleep(interval)
                
                # 检查会话是否仍然存在
                session = await self.session_manager.get_session(session_id)
                if not session:
                    break
                
                # 发送心跳到消息队列
                message_queue = await self.session_manager.get_message_queue(session_id)
                await message_queue.put({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Heartbeat error", session_id=session_id, error=str(e))
    
    def _format_sse_event(self, event_type: str, data: Any, event_id: Optional[str] = None) -> str:
        """格式化SSE事件"""
        lines = []
        
        if event_id:
            lines.append(f"id: {event_id}")
        
        lines.append(f"event: {event_type}")
        lines.append(f"data: {json.dumps(data, ensure_ascii=False)}")
        lines.append(f"retry: {self.settings.sse_retry_interval}")
        lines.append("")  # 空行表示事件结束
        
        return "\n".join(lines) + "\n"
    
    async def _handle_mcp_message(self, session_id: str, message: MCPMessage):
        """处理MCP消息"""
        self.logger.debug("Handling MCP message", 
                         session_id=session_id, 
                         message_type=message.method if hasattr(message, 'method') else 'response')
        
        # 根据消息类型处理
        if isinstance(message, MCPRequest):
            await self._handle_mcp_request(session_id, message)
        elif isinstance(message, MCPResponse):
            await self._handle_mcp_response(session_id, message)
        elif isinstance(message, MCPNotification):
            await self._handle_mcp_notification(session_id, message)
        else:
            self.logger.warning("Unknown MCP message type", 
                              session_id=session_id, 
                              message=message)
    
    async def _handle_mcp_request(self, session_id: str, request: MCPRequest):
        """处理MCP请求"""
        try:
            # 根据方法类型处理
            if request.method == "initialize":
                response = await self._handle_initialize(session_id, request)
            elif request.method == "tools/list":
                response = await self._handle_tools_list(session_id, request)
            elif request.method == "tools/call":
                response = await self._handle_tools_call(session_id, request)
            elif request.method == "resources/list":
                response = await self._handle_resources_list(session_id, request)
            elif request.method == "resources/read":
                response = await self._handle_resources_read(session_id, request)
            elif request.method == "prompts/list":
                response = await self._handle_prompts_list(session_id, request)
            elif request.method == "prompts/get":
                response = await self._handle_prompts_get(session_id, request)
            else:
                # 未知方法
                response = MCPResponse(
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {request.method}"
                    }
                )
            
            # 发送响应
            await self._send_message_to_session(session_id, response.dict())
            
        except Exception as e:
            self.logger.error("Error handling MCP request", 
                            session_id=session_id, 
                            method=request.method, 
                            error=str(e))
            
            # 发送错误响应
            error_response = MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            )
            await self._send_message_to_session(session_id, error_response.dict())
    
    async def _handle_initialize(self, session_id: str, request: MCPRequest) -> MCPResponse:
        """处理初始化请求"""
        # 获取MIRIX的能力信息
        capabilities = await self.mirix_client.get_capabilities()
        
        # 更新服务器信息
        self.server_info["capabilities"] = capabilities
        
        return MCPResponse(
            id=request.id,
            result={
                "protocolVersion": self.server_info["protocolVersion"],
                "capabilities": capabilities,
                "serverInfo": {
                    "name": self.server_info["name"],
                    "version": self.server_info["version"]
                }
            }
        )
    
    async def _handle_tools_list(self, session_id: str, request: MCPRequest) -> MCPResponse:
        """处理工具列表请求"""
        tools = await self.mirix_client.list_tools()
        
        return MCPResponse(
            id=request.id,
            result={"tools": tools}
        )
    
    async def _handle_tools_call(self, session_id: str, request: MCPRequest) -> MCPResponse:
        """处理工具调用请求"""
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        
        # 调用MIRIX工具
        result = await self.mirix_client.call_tool(tool_name, arguments)
        
        return MCPResponse(
            id=request.id,
            result=result
        )
    
    async def _handle_resources_list(self, session_id: str, request: MCPRequest) -> MCPResponse:
        """处理资源列表请求"""
        resources = await self.mirix_client.list_resources()
        
        return MCPResponse(
            id=request.id,
            result={"resources": resources}
        )
    
    async def _handle_resources_read(self, session_id: str, request: MCPRequest) -> MCPResponse:
        """处理资源读取请求"""
        uri = request.params.get("uri")
        
        # 读取MIRIX资源
        content = await self.mirix_client.read_resource(uri)
        
        return MCPResponse(
            id=request.id,
            result={"contents": [content]}
        )
    
    async def _handle_prompts_list(self, session_id: str, request: MCPRequest) -> MCPResponse:
        """处理提示列表请求"""
        prompts = await self.mirix_client.list_prompts()
        
        return MCPResponse(
            id=request.id,
            result={"prompts": prompts}
        )
    
    async def _handle_prompts_get(self, session_id: str, request: MCPRequest) -> MCPResponse:
        """处理提示获取请求"""
        name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        
        # 获取MIRIX提示
        prompt = await self.mirix_client.get_prompt(name, arguments)
        
        return MCPResponse(
            id=request.id,
            result=prompt
        )
    
    async def _handle_mcp_response(self, session_id: str, response: MCPResponse):
        """处理MCP响应"""
        # 响应通常是对之前请求的回复，这里可以做一些处理
        self.logger.debug("Received MCP response", 
                         session_id=session_id, 
                         response_id=response.id)
    
    async def _handle_mcp_notification(self, session_id: str, notification: MCPNotification):
        """处理MCP通知"""
        self.logger.debug("Received MCP notification", 
                         session_id=session_id, 
                         method=notification.method)
        
        # 根据通知类型处理
        if notification.method == "notifications/initialized":
            # 客户端初始化完成
            await self.session_manager.mark_session_initialized(session_id)
        elif notification.method == "notifications/cancelled":
            # 请求被取消
            pass
        # 可以添加更多通知类型的处理
    
    async def _send_message_to_session(self, session_id: str, message: Dict[str, Any]):
        """向会话发送消息"""
        message_queue = await self.session_manager.get_message_queue(session_id)
        await message_queue.put(message)
    
    async def startup(self):
        """服务启动"""
        self.logger.info("Starting MCP SSE Server")
        
        # 初始化MIRIX客户端
        await self.mirix_client.initialize()
        
        # 启动会话管理器
        await self.session_manager.startup()
        
        self.logger.info("MCP SSE Server started successfully")
    
    async def shutdown(self):
        """服务关闭"""
        self.logger.info("Shutting down MCP SSE Server")
        
        # 关闭会话管理器
        await self.session_manager.shutdown()
        
        # 关闭MIRIX客户端
        await self.mirix_client.close()
        
        self.logger.info("MCP SSE Server shut down successfully")