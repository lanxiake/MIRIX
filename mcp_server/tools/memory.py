"""
MIRIX MCP Server - 记忆工具核心模块

该模块是记忆管理系统的核心，整合了所有记忆相关的工具和功能。
提供统一的记忆操作接口，包括添加、搜索、对话和配置文件管理。

主要功能：
1. 记忆添加 - 存储新的记忆信息
2. 记忆搜索 - 检索相关记忆内容
3. 记忆对话 - 基于记忆进行智能对话
4. 配置文件管理 - 获取和更新用户配置
5. 记忆统计 - 提供记忆系统的统计信息
6. 记忆清理 - 管理记忆的生命周期

设计原则：
- 统一接口：所有记忆操作通过统一的接口访问
- 类型安全：严格的参数验证和类型检查
- 错误处理：完善的异常处理和错误恢复
- 性能优化：缓存和批量操作支持
- 扩展性：易于添加新的记忆工具

作者：MIRIX MCP Server Team
版本：1.0.0
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..mirix_adapter import MIRIXAdapter
from ..exceptions import MemoryToolError, ValidationError, handle_exception
from ..utils import measure_time_async, get_logger, validate_required_fields

# 导入具体的记忆工具
from .memory_add import MemoryAddTool, VALID_MEMORY_TYPES
from .memory_search import MemorySearchTool
from .memory_chat import MemoryChatTool
from .memory_get_profile import MemoryGetProfileTool

# 配置日志
logger = get_logger(__name__)


class MemoryOperationType(Enum):
    """记忆操作类型枚举"""
    ADD = "add"
    SEARCH = "search"
    CHAT = "chat"
    GET_PROFILE = "get_profile"
    UPDATE_PROFILE = "update_profile"
    DELETE = "delete"
    CLEAR = "clear"
    STATS = "stats"


@dataclass
class MemoryStats:
    """记忆统计信息"""
    total_memories: int
    memories_by_type: Dict[str, int]
    recent_additions: int
    last_update: datetime
    storage_size: int
    active_sessions: int


@dataclass
class MemorySearchResult:
    """记忆搜索结果"""
    memories: List[Dict[str, Any]]
    total_count: int
    search_time: float
    relevance_scores: List[float]
    suggestions: List[str]


class MemoryManager:
    """
    记忆管理器
    
    统一管理所有记忆相关的操作，提供高级的记忆管理功能。
    作为记忆工具的核心协调器，处理复杂的记忆操作逻辑。
    """
    
    def __init__(self, mirix_adapter: MIRIXAdapter):
        """
        初始化记忆管理器
        
        Args:
            mirix_adapter: MIRIX 客户端适配器
        """
        self.mirix_adapter = mirix_adapter
        
        # 初始化各个记忆工具
        self.add_tool = MemoryAddTool(mirix_adapter)
        self.search_tool = MemorySearchTool(mirix_adapter)
        self.chat_tool = MemoryChatTool(mirix_adapter)
        self.profile_tool = MemoryGetProfileTool(mirix_adapter)
        
        # 缓存配置
        self._stats_cache: Optional[MemoryStats] = None
        self._stats_cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)
        
        logger.info("记忆管理器初始化完成")
    
    @measure_time_async
    async def add_memory(
        self,
        content: str,
        memory_type: str,
        context: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: int = 1
    ) -> Dict[str, Any]:
        """
        添加记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            context: 上下文信息
            tags: 标签列表
            priority: 优先级 (1-5)
            
        Returns:
            Dict[str, Any]: 添加结果
        """
        try:
            logger.info(f"添加记忆: type={memory_type}, priority={priority}")
            
            # 验证参数
            self._validate_memory_type(memory_type)
            self._validate_priority(priority)
            
            # 执行添加操作
            result = await self.add_tool.execute(
                content=content,
                memory_type=memory_type,
                context=context
            )
            
            # 如果有标签，添加标签信息
            if tags and result.get("success"):
                await self._add_memory_tags(
                    result["data"]["memory_id"],
                    tags
                )
            
            # 清除统计缓存
            self._clear_stats_cache()
            
            logger.info(f"记忆添加成功: {result['data']['memory_id']}")
            return result
            
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            return handle_exception(e, "memory_add")
    
    @measure_time_async
    async def search_memories(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10,
        include_context: bool = True,
        min_relevance: float = 0.5
    ) -> MemorySearchResult:
        """
        搜索记忆
        
        Args:
            query: 搜索查询
            memory_types: 限制搜索的记忆类型
            limit: 结果数量限制
            include_context: 是否包含上下文
            min_relevance: 最小相关性阈值
            
        Returns:
            MemorySearchResult: 搜索结果
        """
        try:
            logger.info(f"搜索记忆: query='{query}', limit={limit}")
            
            # 验证参数
            if memory_types:
                for mem_type in memory_types:
                    self._validate_memory_type(mem_type)
            
            # 执行搜索
            start_time = asyncio.get_event_loop().time()
            
            result = await self.search_tool.execute(
                query=query,
                limit=limit
            )
            
            search_time = asyncio.get_event_loop().time() - start_time
            
            # 处理搜索结果
            memories = result.get("data", {}).get("memories", [])
            
            # 过滤记忆类型
            if memory_types:
                memories = [
                    mem for mem in memories
                    if mem.get("memory_type") in memory_types
                ]
            
            # 过滤相关性
            filtered_memories = []
            relevance_scores = []
            
            for memory in memories:
                relevance = memory.get("relevance_score", 1.0)
                if relevance >= min_relevance:
                    filtered_memories.append(memory)
                    relevance_scores.append(relevance)
            
            # 生成搜索建议
            suggestions = await self._generate_search_suggestions(query, memories)
            
            search_result = MemorySearchResult(
                memories=filtered_memories,
                total_count=len(filtered_memories),
                search_time=search_time,
                relevance_scores=relevance_scores,
                suggestions=suggestions
            )
            
            logger.info(f"搜索完成: 找到 {len(filtered_memories)} 条记忆")
            return search_result
            
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            raise MemoryToolError(f"搜索失败: {e}")
    
    @measure_time_async
    async def chat_with_memory(
        self,
        message: str,
        context_limit: int = 5,
        include_profile: bool = True
    ) -> Dict[str, Any]:
        """
        基于记忆进行对话
        
        Args:
            message: 用户消息
            context_limit: 上下文记忆数量限制
            include_profile: 是否包含用户配置文件
            
        Returns:
            Dict[str, Any]: 对话结果
        """
        try:
            logger.info(f"记忆对话: message='{message[:50]}...'")
            
            # 获取相关记忆作为上下文
            search_result = await self.search_memories(
                query=message,
                limit=context_limit,
                include_context=True
            )
            
            # 获取用户配置文件
            profile_data = None
            if include_profile:
                try:
                    profile_result = await self.profile_tool.execute()
                    if profile_result.get("success"):
                        profile_data = profile_result["data"]
                except Exception as e:
                    logger.warning(f"获取用户配置文件失败: {e}")
            
            # 执行对话
            result = await self.chat_tool.execute(
                message=message,
                context_memories=search_result.memories,
                user_profile=profile_data
            )
            
            logger.info("记忆对话完成")
            return result
            
        except Exception as e:
            logger.error(f"记忆对话失败: {e}")
            return handle_exception(e, "memory_chat")
    
    @measure_time_async
    async def get_memory_stats(self, force_refresh: bool = False) -> MemoryStats:
        """
        获取记忆统计信息
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            MemoryStats: 统计信息
        """
        try:
            # 检查缓存
            if not force_refresh and self._is_stats_cache_valid():
                logger.debug("使用缓存的统计信息")
                return self._stats_cache
            
            logger.info("获取记忆统计信息")
            
            # 获取基础统计
            stats_result = await self.mirix_adapter.get_memory_stats()
            
            if not stats_result.get("success"):
                raise MemoryToolError("获取统计信息失败")
            
            stats_data = stats_result["data"]
            
            # 构建统计对象
            stats = MemoryStats(
                total_memories=stats_data.get("total_memories", 0),
                memories_by_type=stats_data.get("memories_by_type", {}),
                recent_additions=stats_data.get("recent_additions", 0),
                last_update=datetime.fromisoformat(
                    stats_data.get("last_update", datetime.now().isoformat())
                ),
                storage_size=stats_data.get("storage_size", 0),
                active_sessions=stats_data.get("active_sessions", 0)
            )
            
            # 更新缓存
            self._stats_cache = stats
            self._stats_cache_time = datetime.now()
            
            logger.info(f"统计信息获取完成: {stats.total_memories} 条记忆")
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise MemoryToolError(f"统计信息获取失败: {e}")
    
    @measure_time_async
    async def clear_memories(
        self,
        memory_types: Optional[List[str]] = None,
        older_than: Optional[datetime] = None,
        confirm: bool = False
    ) -> Dict[str, Any]:
        """
        清理记忆
        
        Args:
            memory_types: 要清理的记忆类型
            older_than: 清理早于此时间的记忆
            confirm: 确认清理操作
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        if not confirm:
            return {
                "success": False,
                "message": "需要确认清理操作",
                "data": {"confirm_required": True}
            }
        
        try:
            logger.warning("开始清理记忆操作")
            
            # 验证记忆类型
            if memory_types:
                for mem_type in memory_types:
                    self._validate_memory_type(mem_type)
            
            # 执行清理
            result = await self.mirix_adapter.clear_memories(
                memory_types=memory_types,
                older_than=older_than.isoformat() if older_than else None
            )
            
            # 清除缓存
            self._clear_stats_cache()
            
            logger.warning(f"记忆清理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"清理记忆失败: {e}")
            return handle_exception(e, "memory_clear")
    
    async def batch_add_memories(
        self,
        memories: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        批量添加记忆
        
        Args:
            memories: 记忆列表
            batch_size: 批处理大小
            
        Returns:
            Dict[str, Any]: 批量添加结果
        """
        try:
            logger.info(f"批量添加 {len(memories)} 条记忆")
            
            results = []
            failed_count = 0
            
            # 分批处理
            for i in range(0, len(memories), batch_size):
                batch = memories[i:i + batch_size]
                batch_results = []
                
                # 并发处理批次
                tasks = []
                for memory in batch:
                    task = self.add_memory(
                        content=memory["content"],
                        memory_type=memory["memory_type"],
                        context=memory.get("context"),
                        tags=memory.get("tags"),
                        priority=memory.get("priority", 1)
                    )
                    tasks.append(task)
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        failed_count += 1
                        results.append({
                            "success": False,
                            "error": str(result)
                        })
                    else:
                        results.append(result)
            
            success_count = len(memories) - failed_count
            
            logger.info(f"批量添加完成: 成功 {success_count}, 失败 {failed_count}")
            
            return {
                "success": True,
                "message": f"批量添加完成: 成功 {success_count}, 失败 {failed_count}",
                "data": {
                    "total": len(memories),
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "results": results
                }
            }
            
        except Exception as e:
            logger.error(f"批量添加记忆失败: {e}")
            return handle_exception(e, "batch_add_memories")
    
    def _validate_memory_type(self, memory_type: str) -> None:
        """验证记忆类型"""
        if memory_type not in VALID_MEMORY_TYPES:
            raise ValidationError(
                f"无效的记忆类型: {memory_type}",
                field_name="memory_type",
                field_value=memory_type,
                valid_values=VALID_MEMORY_TYPES
            )
    
    def _validate_priority(self, priority: int) -> None:
        """验证优先级"""
        if not isinstance(priority, int) or priority < 1 or priority > 5:
            raise ValidationError(
                f"优先级必须是 1-5 之间的整数: {priority}",
                field_name="priority",
                field_value=priority
            )
    
    async def _add_memory_tags(self, memory_id: str, tags: List[str]) -> None:
        """为记忆添加标签"""
        try:
            await self.mirix_adapter.add_memory_tags(memory_id, tags)
        except Exception as e:
            logger.warning(f"添加记忆标签失败: {e}")
    
    async def _generate_search_suggestions(
        self,
        query: str,
        memories: List[Dict[str, Any]]
    ) -> List[str]:
        """生成搜索建议"""
        try:
            # 基于搜索结果生成相关建议
            suggestions = []
            
            # 提取常见关键词
            keywords = set()
            for memory in memories[:5]:  # 只分析前5个结果
                content = memory.get("content", "")
                # 简单的关键词提取（实际应用中可以使用更复杂的NLP技术）
                words = content.lower().split()
                keywords.update([w for w in words if len(w) > 3])
            
            # 生成建议查询
            for keyword in list(keywords)[:3]:
                if keyword not in query.lower():
                    suggestions.append(f"{query} {keyword}")
            
            return suggestions
            
        except Exception as e:
            logger.warning(f"生成搜索建议失败: {e}")
            return []
    
    def _is_stats_cache_valid(self) -> bool:
        """检查统计缓存是否有效"""
        if not self._stats_cache or not self._stats_cache_time:
            return False
        
        return datetime.now() - self._stats_cache_time < self._cache_ttl
    
    def _clear_stats_cache(self) -> None:
        """清除统计缓存"""
        self._stats_cache = None
        self._stats_cache_time = None


# 全局记忆管理器实例
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(mirix_adapter: MIRIXAdapter) -> MemoryManager:
    """
    获取记忆管理器实例
    
    Args:
        mirix_adapter: MIRIX 适配器
        
    Returns:
        MemoryManager: 记忆管理器实例
    """
    global _memory_manager
    
    if _memory_manager is None:
        _memory_manager = MemoryManager(mirix_adapter)
    
    return _memory_manager


# 便捷函数
async def add_memory(
    content: str,
    memory_type: str,
    context: Optional[str] = None,
    mirix_adapter: Optional[MIRIXAdapter] = None
) -> Dict[str, Any]:
    """添加记忆的便捷函数"""
    if not mirix_adapter:
        raise ValueError("需要提供 mirix_adapter")
    
    manager = get_memory_manager(mirix_adapter)
    return await manager.add_memory(content, memory_type, context)


async def search_memories(
    query: str,
    limit: int = 10,
    mirix_adapter: Optional[MIRIXAdapter] = None
) -> MemorySearchResult:
    """搜索记忆的便捷函数"""
    if not mirix_adapter:
        raise ValueError("需要提供 mirix_adapter")
    
    manager = get_memory_manager(mirix_adapter)
    return await manager.search_memories(query, limit=limit)


async def chat_with_memory(
    message: str,
    mirix_adapter: Optional[MIRIXAdapter] = None
) -> Dict[str, Any]:
    """记忆对话的便捷函数"""
    if not mirix_adapter:
        raise ValueError("需要提供 mirix_adapter")
    
    manager = get_memory_manager(mirix_adapter)
    return await manager.chat_with_memory(message)


# 导出的工具元数据
MEMORY_TOOLS_METADATA = {
    "memory_add": {
        "name": "memory_add",
        "description": "向 MIRIX 记忆系统添加新信息",
        "category": "memory",
        "manager_method": "add_memory"
    },
    "memory_search": {
        "name": "memory_search", 
        "description": "在 MIRIX 记忆系统中搜索相关信息",
        "category": "memory",
        "manager_method": "search_memories"
    },
    "memory_chat": {
        "name": "memory_chat",
        "description": "基于记忆进行智能对话",
        "category": "memory", 
        "manager_method": "chat_with_memory"
    },
    "memory_get_profile": {
        "name": "memory_get_profile",
        "description": "获取用户配置文件信息",
        "category": "memory",
        "manager_method": "get_profile"
    }
}