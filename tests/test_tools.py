"""
工具模块单元测试

测试工具注册系统和各种记忆工具的功能，包括：
- 工具注册和发现机制
- 工具参数验证
- 记忆操作工具（添加、搜索、获取配置文件、聊天）
- 错误处理和边界条件
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from mcp_server.tools import (
    tool_registry,
    get_available_tools,
    get_tool_names,
    validate_tool_name,
    get_tool_description,
    get_tool_schema,
    initialize_tools,
    get_mcp_tools_list,
    execute_tool
)
from mcp_server.tools.memory_tools import (
    add_memory_tool,
    search_memory_tool,
    get_memory_profile_tool,
    chat_with_memory_tool
)
from mcp_server.mirix_adapter import MIRIXAdapter
from mcp_server.config import MCPServerConfig
from mcp_server.exceptions import ValidationError, MIRIXAPIError


class TestToolRegistry:
    """工具注册系统测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 清空工具注册表
        tool_registry.clear()
    
    def test_tool_registration(self):
        """测试工具注册"""
        @tool_registry.register("test_tool")
        def test_function():
            """测试函数"""
            return "test result"
        
        assert "test_tool" in tool_registry.tools
        assert tool_registry.tools["test_tool"]["function"] == test_function
        assert tool_registry.tools["test_tool"]["description"] == "测试函数"
    
    def test_tool_registration_with_schema(self):
        """测试带模式的工具注册"""
        schema = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "integer"}
            },
            "required": ["param1"]
        }
        
        @tool_registry.register("test_tool_with_schema", schema=schema)
        def test_function_with_schema(param1: str, param2: int = 10):
            """带参数的测试函数"""
            return f"{param1}:{param2}"
        
        assert "test_tool_with_schema" in tool_registry.tools
        assert tool_registry.tools["test_tool_with_schema"]["schema"] == schema
    
    def test_duplicate_tool_registration(self):
        """测试重复工具注册"""
        @tool_registry.register("duplicate_tool")
        def first_function():
            return "first"
        
        # 重复注册应该覆盖之前的注册
        @tool_registry.register("duplicate_tool")
        def second_function():
            return "second"
        
        assert tool_registry.tools["duplicate_tool"]["function"] == second_function
    
    def test_get_available_tools(self):
        """测试获取可用工具"""
        @tool_registry.register("tool1")
        def func1():
            """工具1"""
            pass
        
        @tool_registry.register("tool2")
        def func2():
            """工具2"""
            pass
        
        tools = get_available_tools()
        assert isinstance(tools, dict)
        assert "tool1" in tools
        assert "tool2" in tools
        assert tools["tool1"]["description"] == "工具1"
        assert tools["tool2"]["description"] == "工具2"
    
    def test_get_tool_names(self):
        """测试获取工具名称列表"""
        @tool_registry.register("tool_a")
        def func_a():
            pass
        
        @tool_registry.register("tool_b")
        def func_b():
            pass
        
        names = get_tool_names()
        assert isinstance(names, list)
        assert "tool_a" in names
        assert "tool_b" in names
        assert len(names) == 2
    
    def test_validate_tool_name(self):
        """测试工具名称验证"""
        @tool_registry.register("valid_tool")
        def valid_func():
            pass
        
        # 有效的工具名称
        assert validate_tool_name("valid_tool") is True
        
        # 无效的工具名称
        assert validate_tool_name("invalid_tool") is False
        assert validate_tool_name("") is False
        assert validate_tool_name(None) is False
    
    def test_get_tool_description(self):
        """测试获取工具描述"""
        @tool_registry.register("described_tool")
        def described_func():
            """这是一个有描述的工具"""
            pass
        
        description = get_tool_description("described_tool")
        assert description == "这是一个有描述的工具"
        
        # 不存在的工具
        assert get_tool_description("nonexistent_tool") is None
    
    def test_get_tool_schema(self):
        """测试获取工具模式"""
        schema = {
            "type": "object",
            "properties": {"param": {"type": "string"}},
            "required": ["param"]
        }
        
        @tool_registry.register("schema_tool", schema=schema)
        def schema_func(param: str):
            pass
        
        retrieved_schema = get_tool_schema("schema_tool")
        assert retrieved_schema == schema
        
        # 不存在的工具
        assert get_tool_schema("nonexistent_tool") is None


class TestMemoryTools:
    """记忆工具测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.config = MCPServerConfig()
        self.mock_adapter = AsyncMock(spec=MIRIXAdapter)
    
    @pytest.mark.asyncio
    async def test_add_memory_tool_success(self):
        """测试成功添加记忆"""
        # 模拟成功响应
        self.mock_adapter.add_memory.return_value = {
            "success": True,
            "data": {
                "id": "memory_123",
                "content": "Test memory content",
                "type": "episodic",
                "user_id": "test_user"
            }
        }
        
        with patch('mcp_server.tools.memory_tools.get_mirix_adapter', return_value=self.mock_adapter):
            result = await add_memory_tool(
                content="Test memory content",
                memory_type="episodic",
                user_id="test_user"
            )
        
        assert result["success"] is True
        assert result["data"]["id"] == "memory_123"
        self.mock_adapter.add_memory.assert_called_once_with(
            content="Test memory content",
            memory_type="episodic",
            user_id="test_user",
            metadata=None
        )
    
    @pytest.mark.asyncio
    async def test_add_memory_tool_with_metadata(self):
        """测试带元数据的记忆添加"""
        metadata = {"source": "test", "importance": "high"}
        
        self.mock_adapter.add_memory.return_value = {
            "success": True,
            "data": {"id": "memory_456"}
        }
        
        with patch('mcp_server.tools.memory_tools.get_mirix_adapter', return_value=self.mock_adapter):
            result = await add_memory_tool(
                content="Test with metadata",
                memory_type="procedural",
                metadata=metadata
            )
        
        assert result["success"] is True
        self.mock_adapter.add_memory.assert_called_once_with(
            content="Test with metadata",
            memory_type="procedural",
            user_id=None,
            metadata=metadata
        )
    
    @pytest.mark.asyncio
    async def test_add_memory_tool_validation_error(self):
        """测试添加记忆的验证错误"""
        self.mock_adapter.add_memory.side_effect = ValidationError("内容不能为空")
        
        with patch('mcp_server.tools.memory_tools.get_mirix_adapter', return_value=self.mock_adapter):
            result = await add_memory_tool(
                content="",
                memory_type="episodic"
            )
        
        assert result["success"] is False
        assert "内容不能为空" in result["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_search_memory_tool_success(self):
        """测试成功搜索记忆"""
        self.mock_adapter.search_memory.return_value = {
            "success": True,
            "data": {
                "results": [
                    {
                        "id": "memory_1",
                        "content": "First result",
                        "score": 0.95,
                        "type": "episodic"
                    },
                    {
                        "id": "memory_2",
                        "content": "Second result", 
                        "score": 0.87,
                        "type": "semantic"
                    }
                ],
                "total": 2,
                "query": "test query"
            }
        }
        
        with patch('mcp_server.tools.memory_tools.get_mirix_adapter', return_value=self.mock_adapter):
            result = await search_memory_tool(
                query="test query",
                memory_types=["episodic", "semantic"],
                limit=10,
                user_id="test_user"
            )
        
        assert result["success"] is True
        assert len(result["data"]["results"]) == 2
        assert result["data"]["total"] == 2
        self.mock_adapter.search_memory.assert_called_once_with(
            query="test query",
            memory_types=["episodic", "semantic"],
            limit=10,
            user_id="test_user",
            filters=None
        )
    
    @pytest.mark.asyncio
    async def test_search_memory_tool_with_filters(self):
        """测试带过滤器的记忆搜索"""
        filters = {"importance": "high", "date_range": "last_week"}
        
        self.mock_adapter.search_memory.return_value = {
            "success": True,
            "data": {"results": [], "total": 0}
        }
        
        with patch('mcp_server.tools.memory_tools.get_mirix_adapter', return_value=self.mock_adapter):
            result = await search_memory_tool(
                query="filtered search",
                memory_types=["episodic"],
                filters=filters
            )
        
        assert result["success"] is True
        self.mock_adapter.search_memory.assert_called_once_with(
            query="filtered search",
            memory_types=["episodic"],
            limit=20,  # 默认值
            user_id=None,
            filters=filters
        )
    
    @pytest.mark.asyncio
    async def test_get_memory_profile_tool_success(self):
        """测试成功获取记忆配置文件"""
        self.mock_adapter.get_memory_profile.return_value = {
            "success": True,
            "data": {
                "user_id": "test_user",
                "total_memories": 150,
                "memory_types": {
                    "episodic": 60,
                    "procedural": 30,
                    "semantic": 40,
                    "resource": 15,
                    "knowledge_vault": 5
                },
                "recent_activity": [
                    {
                        "type": "add",
                        "memory_type": "episodic",
                        "timestamp": "2024-01-01T10:00:00Z"
                    }
                ],
                "statistics": {
                    "avg_memory_size": 256,
                    "most_active_type": "episodic",
                    "last_activity": "2024-01-01T10:00:00Z"
                }
            }
        }
        
        with patch('mcp_server.tools.memory_tools.get_mirix_adapter', return_value=self.mock_adapter):
            result = await get_memory_profile_tool(user_id="test_user")
        
        assert result["success"] is True
        assert result["data"]["user_id"] == "test_user"
        assert result["data"]["total_memories"] == 150
        assert "statistics" in result["data"]
        self.mock_adapter.get_memory_profile.assert_called_once_with(user_id="test_user")
    
    @pytest.mark.asyncio
    async def test_get_memory_profile_tool_default_user(self):
        """测试使用默认用户获取记忆配置文件"""
        self.mock_adapter.get_memory_profile.return_value = {
            "success": True,
            "data": {"user_id": "default_user", "total_memories": 0}
        }
        
        with patch('mcp_server.tools.memory_tools.get_mirix_adapter', return_value=self.mock_adapter):
            result = await get_memory_profile_tool()
        
        assert result["success"] is True
        self.mock_adapter.get_memory_profile.assert_called_once_with(user_id=None)
    
    @pytest.mark.asyncio
    async def test_chat_with_memory_tool_success(self):
        """测试成功的记忆聊天"""
        self.mock_adapter.chat_with_memory.return_value = {
            "success": True,
            "data": {
                "response": "Based on your memories, I can help you with that task.",
                "memory_context": [
                    {
                        "id": "memory_1",
                        "content": "Previous similar task",
                        "relevance_score": 0.92,
                        "type": "procedural"
                    },
                    {
                        "id": "memory_2",
                        "content": "Related knowledge",
                        "relevance_score": 0.85,
                        "type": "semantic"
                    }
                ],
                "conversation_id": "conv_123",
                "context_summary": "Found 2 relevant memories about similar tasks"
            }
        }
        
        with patch('mcp_server.tools.memory_tools.get_mirix_adapter', return_value=self.mock_adapter):
            result = await chat_with_memory_tool(
                message="How do I complete this task?",
                user_id="test_user",
                conversation_id="conv_123"
            )
        
        assert result["success"] is True
        assert "Based on your memories" in result["data"]["response"]
        assert len(result["data"]["memory_context"]) == 2
        assert result["data"]["conversation_id"] == "conv_123"
        self.mock_adapter.chat_with_memory.assert_called_once_with(
            message="How do I complete this task?",
            user_id="test_user",
            conversation_id="conv_123",
            context_limit=5  # 默认值
        )
    
    @pytest.mark.asyncio
    async def test_chat_with_memory_tool_with_context_limit(self):
        """测试带上下文限制的记忆聊天"""
        self.mock_adapter.chat_with_memory.return_value = {
            "success": True,
            "data": {
                "response": "Limited context response",
                "memory_context": [],
                "conversation_id": "new_conv"
            }
        }
        
        with patch('mcp_server.tools.memory_tools.get_mirix_adapter', return_value=self.mock_adapter):
            result = await chat_with_memory_tool(
                message="Simple question",
                context_limit=2
            )
        
        assert result["success"] is True
        self.mock_adapter.chat_with_memory.assert_called_once_with(
            message="Simple question",
            user_id=None,
            conversation_id=None,
            context_limit=2
        )
    
    @pytest.mark.asyncio
    async def test_memory_tool_api_error(self):
        """测试记忆工具API错误处理"""
        self.mock_adapter.add_memory.side_effect = MIRIXAPIError("API服务暂时不可用")
        
        with patch('mcp_server.tools.memory_tools.get_mirix_adapter', return_value=self.mock_adapter):
            result = await add_memory_tool(
                content="Test content",
                memory_type="episodic"
            )
        
        assert result["success"] is False
        assert "API服务暂时不可用" in result["error"]["message"]
        assert result["error"]["code"] == "API_ERROR"


class TestToolExecution:
    """工具执行测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 清空工具注册表
        tool_registry.clear()
        
        # 注册测试工具
        @tool_registry.register("sync_tool")
        def sync_test_tool(param1: str, param2: int = 10):
            """同步测试工具"""
            return f"sync:{param1}:{param2}"
        
        @tool_registry.register("async_tool")
        async def async_test_tool(param1: str):
            """异步测试工具"""
            return f"async:{param1}"
    
    @pytest.mark.asyncio
    async def test_execute_sync_tool(self):
        """测试执行同步工具"""
        result = await execute_tool("sync_tool", {"param1": "test", "param2": 20})
        
        assert result == "sync:test:20"
    
    @pytest.mark.asyncio
    async def test_execute_async_tool(self):
        """测试执行异步工具"""
        result = await execute_tool("async_tool", {"param1": "async_test"})
        
        assert result == "async:async_test"
    
    @pytest.mark.asyncio
    async def test_execute_tool_with_default_params(self):
        """测试使用默认参数执行工具"""
        result = await execute_tool("sync_tool", {"param1": "default_test"})
        
        assert result == "sync:default_test:10"
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """测试执行不存在的工具"""
        with pytest.raises(ValueError) as exc_info:
            await execute_tool("nonexistent_tool", {})
        
        assert "工具 'nonexistent_tool' 不存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_tool_with_error(self):
        """测试工具执行错误"""
        @tool_registry.register("error_tool")
        def error_tool():
            """会出错的工具"""
            raise ValueError("工具执行错误")
        
        with pytest.raises(ValueError) as exc_info:
            await execute_tool("error_tool", {})
        
        assert "工具执行错误" in str(exc_info.value)


class TestToolInitialization:
    """工具初始化测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        tool_registry.clear()
    
    def test_initialize_tools(self):
        """测试工具初始化"""
        # 初始化工具应该注册所有记忆工具
        initialize_tools()
        
        # 检查记忆工具是否已注册
        expected_tools = [
            "add_memory",
            "search_memory", 
            "get_memory_profile",
            "chat_with_memory"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tool_registry.tools
            assert tool_registry.tools[tool_name]["function"] is not None
            assert tool_registry.tools[tool_name]["description"] is not None
    
    def test_get_mcp_tools_list(self):
        """测试获取MCP工具列表"""
        initialize_tools()
        
        tools_list = get_mcp_tools_list()
        
        assert isinstance(tools_list, list)
        assert len(tools_list) > 0
        
        # 检查工具列表格式
        for tool in tools_list:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert isinstance(tool["inputSchema"], dict)


class TestToolIntegration:
    """工具集成测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        tool_registry.clear()
        initialize_tools()
    
    @pytest.mark.asyncio
    async def test_full_memory_workflow_through_tools(self):
        """通过工具测试完整的记忆工作流程"""
        mock_adapter = AsyncMock(spec=MIRIXAdapter)
        
        # 模拟添加记忆
        mock_adapter.add_memory.return_value = {
            "success": True,
            "data": {"id": "memory_123", "content": "Integration test memory"}
        }
        
        # 模拟搜索记忆
        mock_adapter.search_memory.return_value = {
            "success": True,
            "data": {
                "results": [{"id": "memory_123", "content": "Integration test memory", "score": 0.95}],
                "total": 1
            }
        }
        
        # 模拟获取配置文件
        mock_adapter.get_memory_profile.return_value = {
            "success": True,
            "data": {"user_id": "test_user", "total_memories": 1}
        }
        
        # 模拟聊天
        mock_adapter.chat_with_memory.return_value = {
            "success": True,
            "data": {
                "response": "I found your integration test memory.",
                "memory_context": [{"id": "memory_123", "relevance_score": 0.95}]
            }
        }
        
        with patch('mcp_server.tools.memory_tools.get_mirix_adapter', return_value=mock_adapter):
            # 添加记忆
            add_result = await execute_tool("add_memory", {
                "content": "Integration test memory",
                "memory_type": "episodic",
                "user_id": "test_user"
            })
            assert add_result["success"] is True
            
            # 搜索记忆
            search_result = await execute_tool("search_memory", {
                "query": "integration test",
                "memory_types": ["episodic"],
                "user_id": "test_user"
            })
            assert search_result["success"] is True
            assert len(search_result["data"]["results"]) == 1
            
            # 获取配置文件
            profile_result = await execute_tool("get_memory_profile", {
                "user_id": "test_user"
            })
            assert profile_result["success"] is True
            
            # 聊天
            chat_result = await execute_tool("chat_with_memory", {
                "message": "Tell me about my integration test",
                "user_id": "test_user"
            })
            assert chat_result["success"] is True
            assert "integration test memory" in chat_result["data"]["response"]


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])