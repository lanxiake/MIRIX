"""
MIRIX MCP Server - 工具注册模块

该模块提供统一的工具注册和管理功能，负责：
1. 工具的动态注册和发现
2. 工具元数据的管理
3. 工具执行的统一接口
4. 工具权限和验证管理

作者：MIRIX MCP Server Team
版本：1.0.0
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass
from ..exceptions import ToolError, ValidationError, ToolExecutionError
from ..utils import retry_async, measure_time_async

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """工具信息数据类"""
    name: str
    function: Callable
    tool_class: Type
    metadata: Dict[str, Any]
    description: str
    parameters: Dict[str, Any]
    returns: Dict[str, Any]
    examples: List[Dict[str, Any]]
    enabled: bool = True


class ToolRegistry:
    """
    工具注册表
    
    负责管理所有 MCP 工具的注册、发现和执行。
    提供统一的工具管理接口，支持动态工具注册和元数据管理。
    """
    
    def __init__(self):
        """初始化工具注册表"""
        self._tools: Dict[str, ToolInfo] = {}
        self._initialized = False
        logger.info("工具注册表已初始化")
    
    def register_tool(
        self,
        name: str,
        function: Callable,
        tool_class: Type,
        metadata: Dict[str, Any],
        enabled: bool = True
    ) -> None:
        """
        注册工具
        
        Args:
            name: 工具名称
            function: 工具函数
            tool_class: 工具类
            metadata: 工具元数据
            enabled: 是否启用工具
            
        Raises:
            ValidationError: 工具信息验证失败
        """
        try:
            # 验证工具信息
            self._validate_tool_info(name, function, tool_class, metadata)
            
            # 创建工具信息
            tool_info = ToolInfo(
                name=name,
                function=function,
                tool_class=tool_class,
                metadata=metadata,
                description=metadata.get("description", ""),
                parameters=metadata.get("inputSchema", {}).get("properties", {}),
                returns=metadata.get("returns", {}),
                examples=metadata.get("examples", []),
                enabled=enabled
            )
            
            # 注册工具
            self._tools[name] = tool_info
            logger.info(f"工具 '{name}' 注册成功")
            
        except Exception as e:
            logger.error(f"注册工具 '{name}' 失败: {e}")
            raise ValidationError(f"工具注册失败: {e}")
    
    def unregister_tool(self, name: str) -> bool:
        """
        注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"工具 '{name}' 已注销")
            return True
        
        logger.warning(f"尝试注销不存在的工具: {name}")
        return False
    
    def get_tool(self, name: str) -> Optional[ToolInfo]:
        """
        获取工具信息
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[ToolInfo]: 工具信息，不存在则返回 None
        """
        return self._tools.get(name)
    
    def get_tool_function(self, name: str) -> Optional[Callable]:
        """
        获取工具函数
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[Callable]: 工具函数，不存在则返回 None
        """
        tool_info = self._tools.get(name)
        return tool_info.function if tool_info and tool_info.enabled else None
    
    def get_tool_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具元数据
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[Dict]: 工具元数据，不存在则返回 None
        """
        tool_info = self._tools.get(name)
        return tool_info.metadata if tool_info else None
    
    def list_tools(self, enabled_only: bool = True) -> List[str]:
        """
        列出所有工具名称
        
        Args:
            enabled_only: 是否只返回启用的工具
            
        Returns:
            List[str]: 工具名称列表
        """
        if enabled_only:
            return [name for name, info in self._tools.items() if info.enabled]
        return list(self._tools.keys())
    
    def get_all_tools(self, enabled_only: bool = True) -> Dict[str, ToolInfo]:
        """
        获取所有工具信息
        
        Args:
            enabled_only: 是否只返回启用的工具
            
        Returns:
            Dict[str, ToolInfo]: 工具信息字典
        """
        if enabled_only:
            return {name: info for name, info in self._tools.items() if info.enabled}
        return self._tools.copy()
    
    def enable_tool(self, name: str) -> bool:
        """
        启用工具
        
        Args:
            name: 工具名称
            
        Returns:
            bool: 是否成功启用
        """
        tool_info = self._tools.get(name)
        if tool_info:
            tool_info.enabled = True
            logger.info(f"工具 '{name}' 已启用")
            return True
        
        logger.warning(f"尝试启用不存在的工具: {name}")
        return False
    
    def disable_tool(self, name: str) -> bool:
        """
        禁用工具
        
        Args:
            name: 工具名称
            
        Returns:
            bool: 是否成功禁用
        """
        tool_info = self._tools.get(name)
        if tool_info:
            tool_info.enabled = False
            logger.info(f"工具 '{name}' 已禁用")
            return True
        
        logger.warning(f"尝试禁用不存在的工具: {name}")
        return False
    
    @measure_time_async
    async def execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
            **kwargs: 额外参数
            
        Returns:
            Dict[str, Any]: 工具执行结果
            
        Raises:
            ToolExecutionError: 工具执行失败
        """
        tool_info = self._tools.get(name)
        
        if not tool_info:
            raise ToolExecutionError(f"工具 '{name}' 不存在")
        
        if not tool_info.enabled:
            raise ToolExecutionError(f"工具 '{name}' 已禁用")
        
        try:
            logger.info(f"开始执行工具: {name}")
            
            # 执行工具函数
            result = await self._execute_with_retry(
                tool_info.function,
                arguments,
                **kwargs
            )
            
            logger.info(f"工具 '{name}' 执行成功")
            return result
            
        except Exception as e:
            logger.error(f"工具 '{name}' 执行失败: {e}")
            raise ToolExecutionError(f"工具执行失败: {e}")
    
    def initialize_default_tools(self) -> None:
        """
        初始化默认工具
        
        自动注册所有内置的记忆管理工具。
        """
        if self._initialized:
            logger.warning("工具注册表已初始化，跳过重复初始化")
            return
        
        try:
            # 导入工具模块
            from .memory_add import memory_add, MemoryAddTool, TOOL_METADATA as MEMORY_ADD_METADATA
            from .memory_search import memory_search, MemorySearchTool, TOOL_METADATA as MEMORY_SEARCH_METADATA
            from .memory_chat import memory_chat, MemoryChatTool, TOOL_METADATA as MEMORY_CHAT_METADATA
            from .memory_get_profile import memory_get_profile, MemoryGetProfileTool, TOOL_METADATA as MEMORY_GET_PROFILE_METADATA
            
            # 注册所有工具
            tools_to_register = [
                ("memory_add", memory_add, MemoryAddTool, MEMORY_ADD_METADATA),
                ("memory_search", memory_search, MemorySearchTool, MEMORY_SEARCH_METADATA),
                ("memory_chat", memory_chat, MemoryChatTool, MEMORY_CHAT_METADATA),
                ("memory_get_profile", memory_get_profile, MemoryGetProfileTool, MEMORY_GET_PROFILE_METADATA),
            ]
            
            for name, function, tool_class, metadata in tools_to_register:
                self.register_tool(name, function, tool_class, metadata)
            
            self._initialized = True
            logger.info(f"默认工具初始化完成，共注册 {len(tools_to_register)} 个工具")
            
        except Exception as e:
            logger.error(f"初始化默认工具失败: {e}")
            raise ValidationError(f"工具初始化失败: {e}")
    
    def get_mcp_tools_list(self) -> List[Dict[str, Any]]:
        """
        获取 MCP 格式的工具列表
        
        Returns:
            List[Dict]: MCP 工具定义列表
        """
        mcp_tools = []
        
        for name, tool_info in self._tools.items():
            if not tool_info.enabled:
                continue
                
            mcp_tool = {
                "name": name,
                "description": tool_info.description,
                "inputSchema": tool_info.metadata.get("inputSchema", {})
            }
            mcp_tools.append(mcp_tool)
        
        return mcp_tools
    
    def _validate_tool_info(
        self,
        name: str,
        function: Callable,
        tool_class: Type,
        metadata: Dict[str, Any]
    ) -> None:
        """
        验证工具信息
        
        Args:
            name: 工具名称
            function: 工具函数
            tool_class: 工具类
            metadata: 工具元数据
            
        Raises:
            ValidationError: 验证失败
        """
        if not name or not isinstance(name, str):
            raise ValidationError("工具名称必须是非空字符串")
        
        if not callable(function):
            raise ValidationError("工具函数必须是可调用对象")
        
        if not isinstance(tool_class, type):
            raise ValidationError("工具类必须是类型对象")
        
        if not isinstance(metadata, dict):
            raise ValidationError("工具元数据必须是字典")
        
        # 检查必需的元数据字段
        required_fields = ["description", "inputSchema"]
        for field in required_fields:
            if field not in metadata:
                raise ValidationError(f"工具元数据缺少必需字段: {field}")
    
    @retry_async(max_attempts=3, delay=1.0)
    async def _execute_with_retry(
        self,
        function: Callable,
        arguments: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        带重试的工具执行
        
        Args:
            function: 工具函数
            arguments: 参数
            **kwargs: 额外参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 检查函数是否为异步
        import asyncio
        if asyncio.iscoroutinefunction(function):
            return await function(**arguments, **kwargs)
        else:
            return function(**arguments, **kwargs)


# 全局工具注册表实例
tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """
    获取全局工具注册表实例
    
    Returns:
        ToolRegistry: 工具注册表实例
    """
    return tool_registry


def initialize_tools() -> None:
    """
    初始化所有工具
    
    这是一个便捷函数，用于初始化默认工具。
    """
    tool_registry.initialize_default_tools()


# 便捷函数
def register_tool(name: str, function: Callable, tool_class: Type, metadata: Dict[str, Any]) -> None:
    """注册工具的便捷函数"""
    tool_registry.register_tool(name, function, tool_class, metadata)


def get_tool(name: str) -> Optional[ToolInfo]:
    """获取工具的便捷函数"""
    return tool_registry.get_tool(name)


def list_tools() -> List[str]:
    """列出工具的便捷函数"""
    return tool_registry.list_tools()


async def execute_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """执行工具的便捷函数"""
    return await tool_registry.execute_tool(name, arguments)