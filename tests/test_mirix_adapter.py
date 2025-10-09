"""
MIRIX 适配器单元测试

测试 MIRIXAdapter 类的各种功能，包括：
- HTTP 请求处理
- 错误处理和重试机制
- 记忆操作（添加、搜索、获取用户档案、聊天）
- 响应格式化和验证
"""

import os
import sys
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import httpx

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from mcp_server.mirix_adapter import MIRIXAdapter, MIRIXConnectionError, MIRIXAPIError
from mcp_server.config import MCPServerConfig
from mcp_server.exceptions import ValidationError


class TestMIRIXAdapter:
    """测试 MIRIXAdapter 类的基本功能"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.config = MCPServerConfig(
            mirix_backend_url="http://test.example.com:18002",
            mirix_backend_timeout=30,
            default_user_id="test_user"
        )
        self.adapter = MIRIXAdapter(self.config)

    def test_initialization(self):
        """测试适配器初始化"""
        assert self.adapter.config == self.config
        assert self.adapter.base_url == "http://test.example.com:18002"
        assert self.adapter.timeout == 30
        assert not self.adapter._is_initialized

    def test_initialization_with_trailing_slash(self):
        """测试带尾部斜杠的URL初始化"""
        config = MCPServerConfig(mirix_backend_url="http://test.example.com:18002/")
        adapter = MIRIXAdapter(config)
        assert adapter.base_url == "http://test.example.com:18002"

    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """测试成功的HTTP请求"""
        mock_response_data = {"success": True, "data": "test"}
        
        with patch.object(self.adapter, '_ensure_initialized', new_callable=AsyncMock):
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            
            with patch.object(self.adapter, 'client') as mock_client:
                mock_client.get = AsyncMock(return_value=mock_response)
                
                result = await self.adapter._make_request("GET", "/test")
                assert result == mock_response_data
                mock_client.get.assert_called_once_with("/test", params=None)

    @pytest.mark.asyncio
    async def test_make_request_connection_error(self):
        """测试连接错误"""
        with patch.object(self.adapter, '_ensure_initialized'), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get.side_effect = httpx.ConnectError("Connection failed")
            
            self.adapter.client = mock_client_instance
            
            with pytest.raises(MIRIXAPIError):
                await self.adapter._make_request("GET", "/test")

    @pytest.mark.asyncio
    async def test_make_request_http_error(self):
        """测试HTTP错误"""
        with patch.object(self.adapter, '_ensure_initialized', new_callable=AsyncMock):
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=mock_response
            )
            
            with patch.object(self.adapter, 'client') as mock_client:
                mock_client.get = AsyncMock(return_value=mock_response)
                
                with pytest.raises(MIRIXAPIError):
                    await self.adapter._make_request("GET", "/test")

    @pytest.mark.asyncio
    async def test_add_memory_success(self):
        """测试成功添加记忆"""
        memory_data = {
            "content": "这是一个测试记忆",
            "memory_type": "semantic",
            "context": "测试上下文"
        }
        
        mock_response = {"success": True, "message": "记忆添加成功"}
        
        with patch.object(self.adapter, '_make_request', return_value=mock_response):
            result = await self.adapter.add_memory(memory_data)
            
            assert result["success"] is True
            assert result["memory_type"] == "semantic"
            assert result["content"] == "这是一个测试记忆"

    @pytest.mark.asyncio
    async def test_add_memory_validation_error(self):
        """测试添加记忆时的验证错误"""
        memory_data = {}  # 缺少必需的content字段
        
        result = await self.adapter.add_memory(memory_data)
        
        assert result["success"] is False
        assert "记忆内容 (content) 是必需的" in result["error"]

    @pytest.mark.asyncio
    async def test_search_memory_success(self):
        """测试成功搜索记忆"""
        search_data = {
            "query": "测试查询",
            "limit": 5
        }
        
        mock_response = {
            "success": True,
            "results": [
                {"content": "记忆1", "score": 0.9},
                {"content": "记忆2", "score": 0.8}
            ]
        }
        
        with patch.object(self.adapter, '_make_request', return_value=mock_response):
            result = await self.adapter.search_memory(search_data)
            
            assert result["success"] is True
            assert result["query"] == "测试查询"
            assert len(result["results"]["results"]) == 2

    @pytest.mark.asyncio
    async def test_search_memory_validation_error(self):
        """测试搜索记忆时的验证错误"""
        search_data = {}  # 缺少必需的query字段
        
        result = await self.adapter.search_memory(search_data)
        
        assert result["success"] is False
        assert "搜索查询 (query) 是必需的" in result["error"]

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self):
        """测试成功获取用户档案"""
        profile_data = {
            "user_id": "test_user",
            "include_memories": True
        }
        
        mock_response = {
            "success": True,
            "profile": {
                "user_id": "test_user",
                "name": "测试用户",
                "memories_count": 10
            }
        }
        
        with patch.object(self.adapter, '_make_request', return_value=mock_response):
            result = await self.adapter.get_user_profile(profile_data)
            
            assert result["success"] is True
            assert result["user_id"] == "test_user"
            assert result["include_memories"] is True

    @pytest.mark.asyncio
    async def test_chat_with_memory_success(self):
        """测试成功的记忆对话"""
        chat_data = {
            "message": "你好，请告诉我关于测试的信息",
            "context": "测试上下文",
            "use_memory": True
        }
        
        mock_response = {
            "success": True,
            "response": "根据记忆，这里是测试信息..."
        }
        
        with patch.object(self.adapter, '_make_request', return_value=mock_response):
            result = await self.adapter.chat_with_memory(chat_data)
            
            assert result["success"] is True
            assert result["message"] == "你好，请告诉我关于测试的信息"
            assert result["use_memory"] is True

    @pytest.mark.asyncio
    async def test_chat_with_memory_validation_error(self):
        """测试记忆对话时的验证错误"""
        chat_data = {}  # 缺少必需的message字段
        
        result = await self.adapter.chat_with_memory(chat_data)
        
        assert result["success"] is False
        assert "对话消息 (message) 是必需的" in result["error"]

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """测试健康检查成功"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client_instance.get.return_value = mock_response
            
            self.adapter.client = mock_client_instance
            
            result = await self.adapter.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """测试健康检查失败"""
        with patch.object(self.adapter, '_make_request', side_effect=Exception("Health check failed")):
            result = await self.adapter.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_close_session(self):
        """测试关闭会话"""
        mock_client = AsyncMock()
        self.adapter.client = mock_client
        self.adapter._is_initialized = True
        
        await self.adapter.close()
        
        mock_client.aclose.assert_called_once()
        assert not self.adapter._is_initialized

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """测试上下文管理器"""
        with patch.object(self.adapter, 'initialize', return_value=True), \
             patch.object(self.adapter, 'close') as mock_close:
            
            async with self.adapter:
                pass
            
            mock_close.assert_called_once()


class TestMIRIXAdapterIntegration:
    """集成测试"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.config = MCPServerConfig(mirix_backend_url="http://test.example.com:18002")
        self.adapter = MIRIXAdapter(self.config)

    @pytest.mark.asyncio
    async def test_full_memory_workflow(self):
        """测试完整的记忆工作流程"""
        # 模拟添加记忆
        add_response = {"success": True, "message": "记忆添加成功"}
        
        # 模拟搜索记忆
        search_response = {
            "success": True,
            "results": [{"content": "测试记忆", "score": 0.9}]
        }
        
        # 模拟对话
        chat_response = {
            "success": True,
            "response": "基于记忆的回答"
        }
        
        with patch.object(self.adapter, '_make_request', side_effect=[add_response, search_response, chat_response]):
            # 添加记忆
            add_result = await self.adapter.add_memory({
                "content": "测试记忆内容",
                "memory_type": "semantic"
            })
            assert add_result["success"] is True
            
            # 搜索记忆
            search_result = await self.adapter.search_memory({
                "query": "测试",
                "limit": 5
            })
            assert search_result["success"] is True
            
            # 基于记忆对话
            chat_result = await self.adapter.chat_with_memory({
                "message": "告诉我关于测试的信息",
                "use_memory": True
            })
            assert chat_result["success"] is True

    @pytest.mark.asyncio
    async def test_error_handling_chain(self):
        """测试错误处理链"""
        with patch.object(self.adapter, '_make_request', side_effect=Exception("Network error")):
            # 测试各种操作的错误处理
            add_result = await self.adapter.add_memory({"content": "test"})
            assert add_result["success"] is False
            
            search_result = await self.adapter.search_memory({"query": "test"})
            assert search_result["success"] is False
            
            chat_result = await self.adapter.chat_with_memory({"message": "test"})
            assert chat_result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])