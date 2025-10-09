"""MIRIX MCP Server - 工具模块

该模块包含所有 MCP 工具的实现和管理功能。
提供统一的工具接口和注册机制，支持记忆管理相关的各种操作。

主要组件：
1. ToolRegistry - 工具注册和管理
2. 记忆工具 - memory_add, memory_search, memory_chat, memory_get_profile
3. 工具元数据和配置
4. 统一的工具执行接口

使用方式：
```python
from mcp_server.tools import initialize_tools, get_tool_registry

# 初始化工具
initialize_tools()

# 获取工具注册表
registry = get_tool_registry()

# 执行工具
result = await registry.execute_tool("memory_add", {"content": "...", "memory_type": "core"})
```

作者：MIRIX MCP Server Team
版本：1.0.0
"""

from typing import Dict, List, Any, Optional, Type, Callable

from .registry import (
    ToolRegistry,
    ToolInfo,
    tool_registry,
    get_tool_registry,
    initialize_tools,
    register_tool,
    get_tool,
    list_tools,
    execute_tool
)

# 导入记忆工具
from .memory_add import MemoryAddTool, memory_add, TOOL_METADATA as MEMORY_ADD_METADATA
from .memory_search import MemorySearchTool, memory_search, TOOL_METADATA as MEMORY_SEARCH_METADATA
from .memory_chat import MemoryChatTool, memory_chat, TOOL_METADATA as MEMORY_CHAT_METADATA
from .memory_get_profile import MemoryGetProfileTool, memory_get_profile, TOOL_METADATA as MEMORY_GET_PROFILE_METADATA

# 导入记忆管理核心
from .memory import (
    MemoryManager,
    MemoryStats,
    MemorySearchResult,
    MemoryOperationType,
    get_memory_manager,
    add_memory,
    search_memories,
    chat_with_memory,
    MEMORY_TOOLS_METADATA
)

# 工具元数据集合
TOOLS_METADATA = {
    "memory_add": MEMORY_ADD_METADATA,
    "memory_search": MEMORY_SEARCH_METADATA,
    "memory_chat": MEMORY_CHAT_METADATA,
    "memory_get_profile": MEMORY_GET_PROFILE_METADATA
}

# 导出的工具类
TOOL_CLASSES = {
    "memory_add": MemoryAddTool,
    "memory_search": MemorySearchTool,
    "memory_chat": MemoryChatTool,
    "memory_get_profile": MemoryGetProfileTool
}

# 导出的工具函数
TOOL_FUNCTIONS = {
    "memory_add": memory_add,
    "memory_search": memory_search,
    "memory_chat": memory_chat,
    "memory_get_profile": memory_get_profile
}

# 导出的公共接口
__all__ = [
    # 工具注册和管理
    "tool_registry",
    "ToolRegistry", 
    "ToolInfo",
    "initialize_tools",
    "get_mcp_tools_list",
    "execute_tool",
    
    # 工具类
    "MemoryAddTool",
    "MemorySearchTool", 
    "MemoryChatTool",
    "MemoryGetProfileTool",
    "MemoryManager",
    
    # 工具函数
    "add_memory",
    "search_memory",
    "get_memory_profile", 
    "chat_with_memory",
    
    # 元数据和配置
    "TOOLS_METADATA",
    "TOOL_CLASSES",
    "TOOL_FUNCTIONS",
    "MEMORY_TOOLS_METADATA",
    
    # 工具管理函数
    "get_available_tools",
    "get_tool_names",
    "validate_tool_name",
    "get_tool_description",
    "get_tool_schema"
]


# 初始化工具注册表
def initialize_tools():
    """初始化所有工具到注册表"""
    tool_registry.initialize_default_tools()


def get_mcp_tools_list() -> List[Dict[str, Any]]:
    """获取MCP格式的工具列表"""
    return tool_registry.get_mcp_tools()


async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """执行指定的工具"""
    return await tool_registry.execute_tool(tool_name, arguments)


def get_available_tools() -> Dict[str, Dict[str, Any]]:
    """
    获取所有可用工具的信息
    
    Returns:
        Dict[str, Dict[str, Any]]: 工具名称到工具信息的映射
    """
    return {
        name: {
            "metadata": metadata,
            "class": TOOL_CLASSES[name],
            "function": TOOL_FUNCTIONS[name]
        }
        for name, metadata in TOOLS_METADATA.items()
    }


def get_tool_names() -> List[str]:
    """
    获取所有工具名称列表
    
    Returns:
        List[str]: 工具名称列表
    """
    return list(TOOLS_METADATA.keys())


def validate_tool_name(tool_name: str) -> bool:
    """
    验证工具名称是否有效
    
    Args:
        tool_name: 工具名称
        
    Returns:
        bool: 是否为有效的工具名称
    """
    return tool_name in TOOLS_METADATA


def get_tool_description(tool_name: str) -> Optional[str]:
    """
    获取工具描述
    
    Args:
        tool_name: 工具名称
        
    Returns:
        Optional[str]: 工具描述，不存在则返回 None
    """
    metadata = TOOLS_METADATA.get(tool_name)
    return metadata.get("description") if metadata else None


def get_tool_schema(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    获取工具的输入模式
    
    Args:
        tool_name: 工具名称
        
    Returns:
        Optional[Dict[str, Any]]: 工具输入模式，不存在则返回 None
    """
    metadata = TOOLS_METADATA.get(tool_name)
    return metadata.get("inputSchema") if metadata else None