"""
MIRIX 客户端适配器

用于 MCP 服务器与 MIRIX 后端系统的通信适配器。
提供记忆管理、用户档案和系统状态等核心功能的接口。

主要功能：
- 记忆管理（添加、搜索、对话）
- 用户档案管理
- 系统健康检查
- 连接管理和错误处理

设计原则：
- 异步操作，支持高并发
- 完善的错误处理和重试机制
- 连接池管理，提高性能
- 日志记录，便于调试和监控
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
import httpx
from datetime import datetime, timedelta

from .config import MCPServerConfig

logger = logging.getLogger(__name__)


class MIRIXConnectionError(Exception):
    """MIRIX 连接错误"""
    pass


class MIRIXAPIError(Exception):
    """MIRIX API 错误"""
    pass


class MIRIXAdapter:
    """
    MIRIX 后端系统适配器
    
    负责与 MIRIX 后端服务进行通信，提供记忆管理和用户档案等功能。
    采用异步设计，支持连接池和自动重试机制。
    """
    
    def __init__(self, config: MCPServerConfig):
        """
        初始化 MIRIX 适配器
        
        Args:
            config: MCP 服务器配置对象
        """
        self.config = config
        self.base_url = config.mirix_backend_url.rstrip('/')
        self.timeout = 60  # 增加超时时间以支持记忆搜索和复杂操作
        self.client: Optional[httpx.AsyncClient] = None
        self._is_initialized = False
        
        # 连接状态管理
        self._last_health_check = None
        self._health_check_interval = timedelta(minutes=5)
        
    async def initialize(self) -> bool:
        """
        初始化客户端连接
        
        Returns:
            bool: 初始化是否成功
            
        Raises:
            MIRIXConnectionError: 连接失败时抛出
        """
        if self._is_initialized:
            return True
            
        try:
            # 创建 HTTP 客户端
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    "User-Agent": "MIRIX-MCP-Server/1.0.0",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                # 连接池配置
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20
                )
            )
            
            # 执行健康检查
            if await self.health_check():
                self._is_initialized = True
                logger.info(f"MIRIX 适配器初始化成功，连接到: {self.base_url}")
                return True
            else:
                await self.close()
                raise MIRIXConnectionError(f"MIRIX 后端健康检查失败: {self.base_url}")
                
        except Exception as e:
            logger.error(f"MIRIX 适配器初始化失败: {e}")
            await self.close()
            raise MIRIXConnectionError(f"无法连接到 MIRIX 后端: {e}")
    
    async def close(self):
        """关闭客户端连接"""
        if self.client:
            await self.client.aclose()
            self.client = None
        self._is_initialized = False
        logger.info("MIRIX 适配器连接已关闭")
    
    async def _ensure_initialized(self):
        """确保客户端已初始化"""
        if not self._is_initialized:
            await self.initialize()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        发起 HTTP 请求
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            data: 请求数据（JSON）
            params: 查询参数
            retry_count: 重试次数
            
        Returns:
            Dict[str, Any]: 响应数据
            
        Raises:
            MIRIXAPIError: API 请求失败时抛出
        """
        await self._ensure_initialized()
        
        for attempt in range(retry_count):
            try:
                if method.upper() == "GET":
                    response = await self.client.get(endpoint, params=params)
                elif method.upper() == "POST":
                    response = await self.client.post(endpoint, json=data, params=params)
                elif method.upper() == "PUT":
                    response = await self.client.put(endpoint, json=data, params=params)
                elif method.upper() == "DELETE":
                    response = await self.client.delete(endpoint, params=params)
                else:
                    raise ValueError(f"不支持的 HTTP 方法: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP 请求失败: {method} {endpoint} - {e.response.status_code}"
                if attempt == retry_count - 1:
                    logger.error(f"{error_msg} (最终失败)")
                    raise MIRIXAPIError(error_msg)
                else:
                    logger.warning(f"{error_msg} (重试 {attempt + 1}/{retry_count})")
                    await asyncio.sleep(1 * (attempt + 1))  # 指数退避
                    
            except Exception as e:
                error_msg = f"请求错误: {method} {endpoint} - {e}"
                logger.error(f"详细错误信息: {type(e).__name__}: {str(e)}")
                if attempt == retry_count - 1:
                    logger.error(f"{error_msg} (最终失败)")
                    raise MIRIXAPIError(error_msg)
                else:
                    logger.warning(f"{error_msg} (重试 {attempt + 1}/{retry_count})")
                    await asyncio.sleep(1 * (attempt + 1))
    
    async def health_check(self) -> bool:
        """
        执行健康检查
        
        Returns:
            bool: 服务是否健康
        """
        try:
            # 检查是否需要执行健康检查
            now = datetime.now()
            if (self._last_health_check and 
                now - self._last_health_check < self._health_check_interval):
                return True
            
            if not self.client:
                return False
                
            response = await self.client.get("/health", timeout=10)
            is_healthy = response.status_code == 200
            
            if is_healthy:
                self._last_health_check = now
                logger.debug("MIRIX 后端健康检查通过")
            else:
                logger.warning(f"MIRIX 后端健康检查失败: {response.status_code}")
                
            return is_healthy
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False
    
    # ==================== 记忆管理接口 ====================
    
    async def add_memory(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加记忆到 MIRIX 系统
        
        Args:
            memory_data: 记忆数据，包含 content, memory_type, context 等字段
            
        Returns:
            Dict[str, Any]: 添加结果
        """
        try:
            # 验证必需字段
            if "content" not in memory_data:
                raise ValueError("记忆内容 (content) 是必需的")
            
            memory_type = memory_data.get("memory_type", "semantic")
            content = memory_data.get("content", "")
            context = memory_data.get("context", "")
            user_id = memory_data.get("user_id", self.config.default_user_id)
            
            # 构建记忆添加消息
            if context:
                message = f"请记住以下{memory_type}记忆: {content}\n\n上下文: {context}"
            else:
                message = f"请记住以下{memory_type}记忆: {content}"
            
            # 通过 send_message 接口添加记忆
            # 暂时不传递 user_id 参数，因为它导致 ERROR_RESPONSE_FAILED
            request_data = {
                "message": message,
                "memorizing": True
                # "user_id": user_id  # 暂时注释掉，直到修复用户上下文问题
            }
            
            result = await self._make_request("POST", "/send_message", data=request_data)
            
            return {
                "success": True,
                "message": "记忆添加成功",
                "memory_type": memory_type,
                "content": content,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "memory_type": memory_data.get("memory_type", "unknown"),
                "content": memory_data.get("content", "")[:100] + "..."
            }
    
    async def search_memory(self, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        在记忆系统中搜索相关信息
        
        Args:
            search_data: 搜索数据，包含 query, memory_types, limit 等字段
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        try:
            query = search_data.get("query", "")
            if not query:
                raise ValueError("搜索查询 (query) 是必需的")
            
            memory_types = search_data.get("memory_types", [])
            limit = search_data.get("limit", 10)
            user_id = search_data.get("user_id", self.config.default_user_id)
            
            # 构建搜索消息 - 使用MIRIX后端能理解的方式
            if memory_types:
                message = f"请搜索我在{', '.join(memory_types)}记忆中关于'{query}'的相关信息"
            else:
                message = f"请搜索我的记忆中关于'{query}'的相关信息，并告诉我你找到了什么"
            
            request_data = {
                "message": message,
                "memorizing": False  # 搜索时不触发新记忆
                # "user_id": user_id  # 暂时注释掉，直到修复用户上下文问题
            }
            
            result = await self._make_request("POST", "/send_message", data=request_data)
            
            return {
                "success": True,
                "query": query,
                "memory_types": memory_types,
                "limit": limit,
                "results": result
            }
            
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": search_data.get("query", ""),
                "results": []
            }
    
    async def chat_with_memory(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于记忆进行对话
        
        Args:
            chat_data: 对话数据，包含 message, context, use_memory 等字段
            
        Returns:
            Dict[str, Any]: 对话结果
        """
        try:
            message = chat_data.get("message", "")
            if not message:
                raise ValueError("对话消息 (message) 是必需的")
            
            context = chat_data.get("context", "")
            use_memory = chat_data.get("use_memory", True)
            user_id = chat_data.get("user_id", self.config.default_user_id)
            
            # 构建对话请求 - 移除不支持的参数
            if context:
                full_message = f"上下文: {context}\n\n{message}"
            else:
                full_message = message
            
            # 检查消息长度，避免可能导致超时的长消息
            if len(full_message) > 200:
                full_message = full_message[:200] + "..."
                
            request_data = {
                "message": full_message,
                "memorizing": False  # 对话时不强制触发记忆，让Agent自行决定
                # "user_id": user_id  # 暂时注释掉，直到修复用户上下文问题
            }
            
            result = await self._make_request("POST", "/send_message", data=request_data)
            
            return {
                "success": True,
                "message": message,
                "context": context,
                "use_memory": use_memory,
                "response": result
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"记忆对话失败: {e}")
            
            # 如果是超时错误，提供特殊处理
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                return {
                    "success": False,
                    "error": "对话请求超时，可能是后端服务繁忙，请稍后重试",
                    "message": chat_data.get("message", ""),
                    "response": None
                }
            else:
                return {
                    "success": False,
                    "error": error_msg,
                    "message": chat_data.get("message", ""),
                    "response": None
                }
    
    async def get_user_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取用户档案信息
        
        Args:
            profile_data: 档案查询数据，包含 user_id, include_memories 等字段
            
        Returns:
            Dict[str, Any]: 用户档案信息
        """
        try:
            # 确保 profile_data 是字典类型
            if isinstance(profile_data, str):
                profile_data = {"user_id": profile_data}
            elif profile_data is None:
                profile_data = {}
            
            user_id = profile_data.get("user_id", self.config.default_user_id)
            include_memories = profile_data.get("include_memories", True)
            
            # 构建档案查询消息 - 使用自然语言查询方式
            if include_memories:
                message = f"请总结用户 {user_id} 的档案信息，包括我记住的所有相关记忆和信息"
            else:
                message = f"请总结用户 {user_id} 的基本档案信息"
            
            request_data = {
                "message": message,
                "memorizing": False  # 档案查询不触发新记忆
                # "user_id": user_id  # 暂时注释掉，直到修复用户上下文问题
            }
            
            result = await self._make_request("POST", "/send_message", data=request_data)
            
            return {
                "success": True,
                "user_id": user_id,
                "include_memories": include_memories,
                "profile": result
            }
            
        except Exception as e:
            logger.error(f"获取用户档案失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": profile_data.get("user_id", "unknown"),
                "profile": None
            }
    
    # ==================== 系统状态接口 ====================
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态信息
        
        Returns:
            Dict[str, Any]: 系统状态
        """
        try:
            # 获取健康状态
            health_status = await self.health_check()
            
            # 获取系统信息（如果有相应的 API）
            system_info = {
                "backend_url": self.base_url,
                "health_status": health_status,
                "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None,
                "connection_initialized": self._is_initialized
            }
            
            return {
                "success": True,
                "status": system_info
            }
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": None
            }
    
    # ==================== 上下文管理器支持 ====================
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()