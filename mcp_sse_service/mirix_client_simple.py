"""
简化的 MIRIX 客户端

专门用于 MCP 服务器，提供基本的记忆管理功能。
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import httpx
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class MIRIXClient:
    """简化的 MIRIX 后端客户端"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None

    async def initialize(self):
        """初始化客户端连接"""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "User-Agent": "MIRIX-MCP-Server/1.0.0",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )

        # 测试连接
        try:
            response = await self.client.get("/health")
            if response.status_code == 200:
                logger.info(f"Successfully connected to MIRIX backend at {self.base_url}")
                return True
            else:
                logger.warning(f"MIRIX backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to MIRIX backend: {e}")
            raise

    async def close(self):
        """关闭客户端连接"""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def _make_request(self, method: str, endpoint: str,
                           data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发起 HTTP 请求"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        try:
            if method.upper() == "GET":
                response = await self.client.get(endpoint, params=data)
            elif method.upper() == "POST":
                response = await self.client.post(endpoint, json=data)
            elif method.upper() == "PUT":
                response = await self.client.put(endpoint, json=data)
            elif method.upper() == "DELETE":
                response = await self.client.delete(endpoint)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP request failed: {method} {endpoint} - {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Request error: {method} {endpoint} - {e}")
            raise

    async def add_memory(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加记忆到 MIRIX 系统"""
        try:
            # 使用实际的 MIRIX API - 通过 send_message 接口
            memory_type = memory_data.get("memory_type", "semantic")
            content = memory_data.get("content", "")
            context = memory_data.get("context", "")

            # 构建记忆添加消息
            if context:
                message = f"请记住以下{memory_type}记忆: {content}\n\n上下文: {context}"
            else:
                message = f"请记住以下{memory_type}记忆: {content}"

            message_request = {
                "message": message,
                "memorizing": True,
                "user_id": memory_data.get("user_id")
            }

            result = await self._make_request("POST", "/send_message", message_request)

            # 模拟成功的记忆添加响应
            return {
                "memory_id": f"mem_{hash(content)}",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            raise

    async def search_memory(self, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """搜索用户记忆"""
        try:
            # 使用实际的记忆端点进行搜索
            memory_types = search_data.get("memory_types", [])
            query = search_data.get("query", "")
            limit = search_data.get("limit", 10)

            memories = []

            # 搜索不同类型的记忆
            if not memory_types or "episodic" in memory_types:
                episodic = await self._make_request("GET", "/memory/episodic")
                for item in episodic[:limit//6 if memory_types else limit]:
                    if query.lower() in item.get("summary", "").lower() or query.lower() in item.get("details", "").lower():
                        memories.append({
                            "type": "episodic",
                            "content": item.get("summary", ""),
                            "timestamp": item.get("timestamp")
                        })

            if not memory_types or "semantic" in memory_types:
                semantic = await self._make_request("GET", "/memory/semantic")
                for item in semantic[:limit//6 if memory_types else limit]:
                    if query.lower() in item.get("title", "").lower() or query.lower() in item.get("summary", "").lower():
                        memories.append({
                            "type": "semantic",
                            "content": item.get("summary", ""),
                            "title": item.get("title")
                        })

            if not memory_types or "core" in memory_types:
                core = await self._make_request("GET", "/memory/core")
                for item in core[:limit//6 if memory_types else limit]:
                    if query.lower() in item.get("understanding", "").lower():
                        memories.append({
                            "type": "core",
                            "content": item.get("understanding", ""),
                            "aspect": item.get("aspect")
                        })

            return {
                "memories": memories[:limit],
                "total_count": len(memories)
            }
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            # 返回空结果而不是抛出异常
            return {
                "memories": [],
                "total_count": 0
            }

    async def send_chat_message(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送聊天消息并处理记忆"""
        try:
            # 使用实际的 MIRIX send_message API
            message_request = {
                "message": chat_data.get("message", ""),
                "memorizing": chat_data.get("memorizing", True),
                "user_id": chat_data.get("user_id")
            }

            if chat_data.get("image_uris"):
                message_request["image_uris"] = chat_data["image_uris"]

            result = await self._make_request("POST", "/send_message", message_request)

            return {
                "response": result.get("response", ""),
                "memorized": True,
                "memory_updates": []
            }
        except Exception as e:
            logger.error(f"Failed to send chat message: {e}")
            raise

    async def get_user_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取用户档案"""
        try:
            # 获取各种记忆类型来构建用户档案
            core_memory = await self._make_request("GET", "/memory/core")
            episodic_memory = await self._make_request("GET", "/memory/episodic")
            semantic_memory = await self._make_request("GET", "/memory/semantic")

            profile = {
                "profile": {
                    "core_understanding": core_memory,
                    "recent_activities": episodic_memory[:5],
                    "knowledge_areas": semantic_memory[:5]
                },
                "memory_summary": {
                    "core": len(core_memory),
                    "episodic": len(episodic_memory),
                    "semantic": len(semantic_memory)
                },
                "total_memories": len(core_memory) + len(episodic_memory) + len(semantic_memory),
                "last_updated": datetime.utcnow().isoformat()
            }

            return profile
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            # 返回空档案而不是抛出异常
            return {
                "profile": {},
                "memory_summary": {},
                "total_memories": 0,
                "last_updated": datetime.utcnow().isoformat()
            }

    async def get_mcp_status(self) -> Dict[str, Any]:
        """获取 MCP 状态信息"""
        try:
            # 获取基本的服务器状态
            result = await self._make_request("GET", "/health")

            # 添加更多状态信息
            status = {
                "status": "connected",
                "backend_url": self.base_url,
                "health": result,
                "timestamp": datetime.utcnow().isoformat()
            }

            return status
        except Exception as e:
            logger.error(f"Failed to get MCP status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            response = await self._make_request("GET", "/health")
            return response.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False