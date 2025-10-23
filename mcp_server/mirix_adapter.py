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
        self.timeout = 600  # 延长超时时间到 10 分钟以支持后端长时间处理
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

    async def get_user_id_from_name(self, username: str) -> Optional[str]:
        """
        根据用户名获取用户的数据库 UUID

        Args:
            username: 用户名

        Returns:
            Optional[str]: 用户的 UUID，如果不存在返回 None
        """
        try:
            await self._ensure_initialized()

            # 调用后端 API 获取用户列表
            response = await self.client.get("/users")
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])

                # 查找匹配的用户名
                for user in users:
                    if user.get("name") == username:
                        user_id = user.get("id")
                        logger.debug(f"用户名映射: {username} -> {user_id}")
                        return user_id

                logger.warning(f"未找到用户名: {username}")
                return None
            else:
                logger.error(f"获取用户列表失败: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"查询用户ID失败: {e}")
            return None

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
            user_id_or_name = memory_data.get("user_id", self.config.default_user_id)

            # 将用户名映射为 UUID（如果需要）
            user_id = await self.get_user_id_from_name(user_id_or_name)
            if not user_id:
                # 如果映射失败，尝试直接使用原值（可能本身就是 UUID）
                user_id = user_id_or_name
                logger.warning(f"用户名映射失败，使用原值: {user_id_or_name}")

            # 构建记忆添加消息
            if context:
                message = f"请记住以下{memory_type}记忆: {content}\n\n上下文: {context}"
            else:
                message = f"请记住以下{memory_type}记忆: {content}"

            # 通过 send_message 接口添加记忆
            request_data = {
                "message": message,
                "memorizing": True,
                "user_id": user_id  # 传递数据库 UUID
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
            user_id_or_name = search_data.get("user_id", self.config.default_user_id)

            # 将用户名映射为 UUID（如果需要）
            user_id = await self.get_user_id_from_name(user_id_or_name)
            if not user_id:
                # 如果映射失败，尝试直接使用原值（可能本身就是 UUID）
                user_id = user_id_or_name
                logger.warning(f"用户名映射失败，使用原值: {user_id_or_name}")

            # 构建搜索消息 - 使用MIRIX后端能理解的方式
            if memory_types:
                message = f"请搜索我在{', '.join(memory_types)}记忆中关于'{query}'的相关信息"
            else:
                message = f"请搜索我的记忆中关于'{query}'的相关信息，并告诉我你找到了什么"

            request_data = {
                "message": message,
                "memorizing": False,  # 搜索时不触发新记忆
                "user_id": user_id  # 传递数据库 UUID
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
            user_id_or_name = chat_data.get("user_id", self.config.default_user_id)

            # 将用户名映射为 UUID（如果需要）
            user_id = await self.get_user_id_from_name(user_id_or_name)
            if not user_id:
                # 如果映射失败，尝试直接使用原值（可能本身就是 UUID）
                user_id = user_id_or_name
                logger.warning(f"用户名映射失败，使用原值: {user_id_or_name}")

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
                "memorizing": False,  # 对话时不强制触发记忆，让Agent自行决定
                "user_id": user_id  # 传递数据库 UUID
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
    
    # ==================== 分类记忆查询接口 ====================
    
    async def get_episodic_memory(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取情景记忆（过去发生的事件）
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            Dict[str, Any]: 情景记忆列表
        """
        try:
            result = await self._make_request("GET", "/memory/episodic")
            return {
                "success": True,
                "memory_type": "episodic",
                "memories": result if isinstance(result, list) else [],
                "count": len(result) if isinstance(result, list) else 0
            }
        except Exception as e:
            logger.error(f"获取情景记忆失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "memory_type": "episodic",
                "memories": [],
                "count": 0
            }
    
    async def get_semantic_memory(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取语义记忆（知识和概念）
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            Dict[str, Any]: 语义记忆列表
        """
        try:
            result = await self._make_request("GET", "/memory/semantic")
            return {
                "success": True,
                "memory_type": "semantic",
                "memories": result if isinstance(result, list) else [],
                "count": len(result) if isinstance(result, list) else 0
            }
        except Exception as e:
            logger.error(f"获取语义记忆失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "memory_type": "semantic",
                "memories": [],
                "count": 0
            }
    
    async def get_procedural_memory(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取程序记忆（技能和步骤）
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            Dict[str, Any]: 程序记忆列表
        """
        try:
            result = await self._make_request("GET", "/memory/procedural")
            return {
                "success": True,
                "memory_type": "procedural",
                "memories": result if isinstance(result, list) else [],
                "count": len(result) if isinstance(result, list) else 0
            }
        except Exception as e:
            logger.error(f"获取程序记忆失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "memory_type": "procedural",
                "memories": [],
                "count": 0
            }
    
    async def get_resource_memory(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取资源记忆（文档和文件）
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            Dict[str, Any]: 资源记忆列表
        """
        try:
            result = await self._make_request("GET", "/memory/resources")
            return {
                "success": True,
                "memory_type": "resource",
                "memories": result if isinstance(result, list) else [],
                "count": len(result) if isinstance(result, list) else 0
            }
        except Exception as e:
            logger.error(f"获取资源记忆失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "memory_type": "resource",
                "memories": [],
                "count": 0
            }
    
    async def get_core_memory(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取核心记忆（对用户的核心理解）
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            Dict[str, Any]: 核心记忆列表
        """
        try:
            result = await self._make_request("GET", "/memory/core")
            return {
                "success": True,
                "memory_type": "core",
                "memories": result if isinstance(result, list) else [],
                "count": len(result) if isinstance(result, list) else 0
            }
        except Exception as e:
            logger.error(f"获取核心记忆失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "memory_type": "core",
                "memories": [],
                "count": 0
            }
    
    async def get_credentials_memory(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取凭证记忆（知识库，敏感信息已加密）
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            Dict[str, Any]: 凭证记忆列表
        """
        try:
            result = await self._make_request("GET", "/memory/credentials")
            return {
                "success": True,
                "memory_type": "credentials",
                "memories": result if isinstance(result, list) else [],
                "count": len(result) if isinstance(result, list) else 0
            }
        except Exception as e:
            logger.error(f"获取凭证记忆失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "memory_type": "credentials",
                "memories": [],
                "count": 0
            }
    
    async def search_memories_by_types(
        self, 
        query: str, 
        memory_types: List[str], 
        limit: int = 10,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        根据记忆类型搜索记忆
        
        Args:
            query: 搜索查询字符串
            memory_types: 要搜索的记忆类型列表
            limit: 每种类型的结果数量限制
            user_id: 用户ID（可选）
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        try:
            all_memories = []
            search_results = {}
            
            # 定义记忆类型到方法的映射
            type_methods = {
                "episodic": self.get_episodic_memory,
                "semantic": self.get_semantic_memory,
                "procedural": self.get_procedural_memory,
                "resource": self.get_resource_memory,
                "core": self.get_core_memory,
                "credentials": self.get_credentials_memory
            }
            
            # 为每种记忆类型获取数据
            for memory_type in memory_types:
                if memory_type in type_methods:
                    try:
                        result = await type_methods[memory_type](user_id)
                        if result.get("success"):
                            memories = result.get("memories", [])
                            # 简单的关键字过滤
                            filtered_memories = self._filter_memories_by_query(memories, query)
                            # 限制结果数量
                            limited_memories = filtered_memories[:limit]
                            
                            search_results[memory_type] = {
                                "memories": limited_memories,
                                "count": len(limited_memories),
                                "total_available": len(memories)
                            }
                            
                            # 为每个记忆添加类型标识
                            for memory in limited_memories:
                                memory["memory_type"] = memory_type
                                all_memories.append(memory)
                        else:
                            search_results[memory_type] = {
                                "memories": [],
                                "count": 0,
                                "error": result.get("error", "未知错误")
                            }
                    except Exception as e:
                        logger.warning(f"搜索 {memory_type} 记忆时出错: {e}")
                        search_results[memory_type] = {
                            "memories": [],
                            "count": 0,
                            "error": str(e)
                        }
            
            return {
                "success": True,
                "query": query,
                "memory_types": memory_types,
                "results": search_results,
                "all_memories": all_memories,
                "total_count": len(all_memories)
            }
            
        except Exception as e:
            logger.error(f"按类型搜索记忆失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "memory_types": memory_types,
                "results": {},
                "all_memories": [],
                "total_count": 0
            }
    
    async def search_memories_by_vector(
        self, 
        query: str, 
        memory_types: List[str], 
        limit: int = 10,
        user_id: Optional[str] = None,
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        使用多种搜索策略搜索记忆，优先使用BM25，fallback到向量搜索
        
        Args:
            query: 搜索查询字符串
            memory_types: 要搜索的记忆类型列表
            limit: 每种类型的结果数量限制
            user_id: 用户ID（可选）
            similarity_threshold: 相似度阈值（0-1，越高越严格）
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        try:
            logger.info(f"开始多策略搜索: query='{query}', types={memory_types}, limit={limit}, threshold={similarity_threshold}")
            
            all_memories = []
            search_results = {}
            
            # 定义记忆类型到后端API路径的映射
            type_api_paths = {
                "episodic": "/memories/episodic/search",
                "semantic": "/memories/semantic/search", 
                "procedural": "/memories/procedural/search",
                "resource": "/memories/resource/search",
                "core": "/memories/core/search",
                "credentials": "/memories/credentials/search"
            }
            
            # 为每种记忆类型执行多策略搜索
            for memory_type in memory_types:
                if memory_type in type_api_paths:
                    memories_found = []
                    search_method_used = "none"
                    error_msg = None
                    
                    # 策略1: 首先尝试BM25搜索（像memory_chat一样）
                    try:
                        logger.debug(f"尝试BM25搜索 {memory_type} 记忆...")
                        
                        bm25_request = {
                            "query": query,
                            "search_method": "bm25",  # 使用BM25搜索
                            "search_field": self._get_default_search_field(memory_type),
                            "limit": limit
                        }
                        
                        # 只有当user_id不是默认值时才传递，让后端使用当前活跃用户
                        if user_id and user_id != self.config.default_user_id:
                            bm25_request["user_id"] = user_id
                        
                        logger.debug(f"发送BM25搜索请求到 {type_api_paths[memory_type]}: {bm25_request}")
                        
                        result = await self._make_request(
                            "POST", 
                            type_api_paths[memory_type], 
                            data=bm25_request
                        )
                        
                        if result and isinstance(result, list) and len(result) > 0:
                            # BM25搜索成功
                            for memory in result:
                                memory["memory_type"] = memory_type
                                # BM25搜索给予较高的默认分数
                                if "similarity_score" not in memory:
                                    memory["similarity_score"] = 0.8
                                memories_found.append(memory)
                            
                            search_method_used = "bm25"
                            logger.info(f"{memory_type} BM25搜索成功，找到 {len(memories_found)} 条记忆")
                        
                    except Exception as e:
                        logger.warning(f"BM25搜索 {memory_type} 失败: {e}")
                    
                    # 策略2: 如果BM25没有结果，尝试向量搜索但降低阈值
                    if not memories_found:
                        try:
                            logger.debug(f"BM25无结果，尝试向量搜索 {memory_type} 记忆...")
                            
                            # 降低向量搜索的阈值
                            vector_threshold = max(0.3, similarity_threshold - 0.3)
                            
                            vector_request = {
                                "query": query,
                                "search_method": "embedding",  # 使用向量搜索
                                "search_field": self._get_default_search_field(memory_type),
                                "limit": limit,
                                "similarity_threshold": vector_threshold
                            }
                            
                            if user_id and user_id != self.config.default_user_id:
                                vector_request["user_id"] = user_id
                            
                            logger.debug(f"发送向量搜索请求到 {type_api_paths[memory_type]}: {vector_request}")
                            
                            result = await self._make_request(
                                "POST", 
                                type_api_paths[memory_type], 
                                data=vector_request
                            )
                            
                            if result and isinstance(result, list):
                                # 为每个记忆添加类型标识和相似度分数
                                for memory in result:
                                    memory["memory_type"] = memory_type
                                    # 如果后端返回了相似度分数，保留它
                                    if "similarity_score" not in memory:
                                        memory["similarity_score"] = 0.5  # 向量搜索默认分数
                                    
                                    # 应用降低后的相似度阈值过滤
                                    if memory["similarity_score"] >= vector_threshold:
                                        memories_found.append(memory)
                                
                                if memories_found:
                                    search_method_used = f"embedding(threshold={vector_threshold})"
                                    logger.info(f"{memory_type} 向量搜索成功，找到 {len(result)} 条记忆，过滤后 {len(memories_found)} 条")
                                else:
                                    logger.info(f"{memory_type} 向量搜索找到 {len(result)} 条记忆，但都被阈值过滤")
                            
                        except Exception as e:
                            logger.warning(f"向量搜索 {memory_type} 失败: {e}")
                            error_msg = str(e)
                    
                    # 策略3: 如果向量搜索也失败，尝试简单的字符串匹配
                    if not memories_found:
                        try:
                            logger.debug(f"向量搜索无结果，尝试字符串匹配搜索 {memory_type} 记忆...")
                            
                            string_request = {
                                "query": query,
                                "search_method": "string_match",  # 使用字符串匹配
                                "search_field": self._get_default_search_field(memory_type),
                                "limit": limit
                            }
                            
                            if user_id and user_id != self.config.default_user_id:
                                string_request["user_id"] = user_id
                            
                            logger.debug(f"发送字符串匹配请求到 {type_api_paths[memory_type]}: {string_request}")
                            
                            result = await self._make_request(
                                "POST", 
                                type_api_paths[memory_type], 
                                data=string_request
                            )
                            
                            if result and isinstance(result, list) and len(result) > 0:
                                for memory in result:
                                    memory["memory_type"] = memory_type
                                    # 字符串匹配给予中等分数
                                    if "similarity_score" not in memory:
                                        memory["similarity_score"] = 0.6
                                    memories_found.append(memory)
                                
                                search_method_used = "string_match"
                                logger.info(f"{memory_type} 字符串匹配成功，找到 {len(memories_found)} 条记忆")
                            
                        except Exception as e:
                            logger.warning(f"字符串匹配搜索 {memory_type} 失败: {e}")
                            if not error_msg:
                                error_msg = str(e)
                    
                    # 记录搜索结果
                    if memories_found:
                        search_results[memory_type] = {
                            "memories": memories_found,
                            "count": len(memories_found),
                            "method": search_method_used,
                            "success": True
                        }
                        all_memories.extend(memories_found)
                    else:
                        search_results[memory_type] = {
                            "memories": [],
                            "count": 0,
                            "method": "all_failed",
                            "error": error_msg or "所有搜索策略都未找到结果"
                        }
                        
                else:
                    logger.warning(f"不支持的记忆类型: {memory_type}")
                    search_results[memory_type] = {
                        "memories": [],
                        "count": 0,
                        "method": "unsupported",
                        "error": f"不支持的记忆类型: {memory_type}"
                    }
            
            # 按相似度分数排序所有记忆
            all_memories.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            
            logger.info(f"多策略搜索完成，总共找到 {len(all_memories)} 条记忆")
            
            return {
                "success": True,
                "query": query,
                "memory_types": memory_types,
                "search_method": "multi_strategy",
                "similarity_threshold": similarity_threshold,
                "results": search_results,
                "all_memories": all_memories,
                "total_count": len(all_memories)
            }
            
        except Exception as e:
            logger.error(f"多策略搜索失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "memory_types": memory_types,
                "search_method": "multi_strategy",
                "results": {},
                "all_memories": [],
                "total_count": 0
            }
    
    def _filter_memories_by_query(self, memories: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        根据查询字符串过滤记忆，支持多关键词搜索
        
        Args:
            memories: 记忆列表
            query: 查询字符串，多个关键词用空格分隔
                  例如: "电脑 水果" 将搜索同时包含"电脑"和"水果"的记忆
            
        Returns:
            List[Dict[str, Any]]: 过滤后的记忆列表
        """
        if not query or not memories:
            return memories
        
        # 将查询字符串分割为多个关键词，去除空白
        keywords = [keyword.strip().lower() for keyword in query.split() if keyword.strip()]
        if not keywords:
            return memories
        
        filtered_memories = []
        
        for memory in memories:
            # 获取所有可搜索字段的文本内容
            searchable_fields = [
                memory.get("summary", ""),
                memory.get("details", ""),
                memory.get("content", ""),
                memory.get("title", ""),
                memory.get("filename", ""),
                memory.get("name", ""),
                str(memory.get("tree_path", [])),
            ]
            
            # 将所有字段合并为一个搜索文本
            combined_text = " ".join(str(field) for field in searchable_fields).lower()
            
            # 检查是否所有关键词都在文本中出现（AND模式）
            all_keywords_found = all(keyword in combined_text for keyword in keywords)
            
            if all_keywords_found:
                filtered_memories.append(memory)
        
        return filtered_memories
    
    async def upload_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        上传文档到资源记忆系统
        
        Args:
            document_data: 文档数据，包含 file_name, file_type, content 等字段
            
        Returns:
            Dict[str, Any]: 上传结果
        """
        try:
            # 验证必需字段
            required_fields = ["file_name", "file_type", "content"]
            for field in required_fields:
                if field not in document_data:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 构建上传请求数据
            # 需要将文本内容编码为Base64，因为后端API期望Base64格式
            import base64
            content = document_data["content"]
            
            # 确保内容是字符串类型
            if not isinstance(content, str):
                content = str(content)
            
            # 将字符串编码为UTF-8字节，然后转换为Base64
            try:
                content_bytes = content.encode('utf-8')
                base64_content = base64.b64encode(content_bytes).decode('ascii')
                logger.debug(f"成功将内容编码为Base64，原始长度: {len(content)}, 编码后长度: {len(base64_content)}")
            except Exception as e:
                logger.error(f"Base64编码失败: {e}")
                raise ValueError(f"文件内容编码失败: {e}")
            
            upload_request = {
                "file_name": document_data["file_name"],
                "file_type": document_data["file_type"],
                "content": base64_content,  # 使用Base64编码的内容
                "user_id": document_data.get("user_id"),
                "description": document_data.get("description")
            }
            
            result = await self._make_request("POST", "/documents/upload", data=upload_request)
            
            return {
                "success": True,
                "message": "文档上传成功",
                "document_id": result.get("document_id"),
                "processed_content": result.get("processed_content"),
                "upload_result": result
            }
            
        except Exception as e:
            logger.error(f"文档上传失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "文档上传失败"
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

    def _get_default_search_field(self, memory_type: str) -> str:
        """
        获取每种记忆类型的默认搜索字段
        
        Args:
            memory_type: 记忆类型
            
        Returns:
            str: 默认搜索字段名
        """
        default_fields = {
            "episodic": "details",      # 情景记忆搜索详情字段
            "semantic": "details",      # 语义记忆搜索详情字段  
            "procedural": "summary",    # 程序记忆搜索描述字段
            "resource": "summary",      # 资源记忆搜索摘要字段（使用summary_embedding）
            "core": "value",           # 核心记忆搜索值字段
            "credentials": "caption"    # 凭证记忆搜索标题字段
        }
        return default_fields.get(memory_type, "summary")