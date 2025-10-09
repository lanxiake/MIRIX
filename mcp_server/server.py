"""
MCP Server 核心实现 - 纯SSE模式

基于 FastMCP 的服务器实现，专注于 SSE (Server-Sent Events) 传输模式。
提供与 MIRIX 后端的集成功能，包括记忆管理、搜索和工具调用。
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP
from mcp.types import (
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .config import MCPServerConfig
from .mirix_adapter import MIRIXAdapter

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP 服务器 - 基于 FastMCP 的实现

    使用 FastMCP 简化的 MCP 服务器，提供完整的工具调用和记忆管理功能。
    """

    def __init__(self, config: MCPServerConfig):
        """初始化 MCP 服务器

        Args:
            config: 服务器配置
        """
        self.config = config

        # 创建 FastMCP 实例
        self.mcp = FastMCP(config.server_name)

        # 初始化 MIRIX 适配器
        self.mirix_adapter = MIRIXAdapter(config)

        # 设置工具
        self._setup_tools()

        logger.info(f"MCP Server 初始化完成 - {config.server_name} v{config.server_version}")
        logger.info(f"SSE 模式配置: {config.sse_host}:{config.sse_port}")

    def _setup_tools(self):
        """设置 MCP 工具"""

        @self.mcp.tool(
            name="memory_add",
            description="向记忆系统添加新信息"
        )
        async def memory_add(content: str, user_id: str = None) -> str:
            """添加记忆"""
            try:
                if not user_id:
                    user_id = self.config.default_user_id

                logger.info(f"添加记忆: user_id={user_id}, content={content[:100]}...")

                # 调用MIRIX适配器添加记忆
                memory_data = {
                    "content": content,
                    "user_id": user_id,
                    "memory_type": "semantic"
                }
                result = await self.mirix_adapter.add_memory(memory_data)

                if result.get("success"):
                    return f"成功添加记忆: {result.get('message', '记忆已保存')}"
                else:
                    return f"添加记忆失败: {result.get('error', '未知错误')}"

            except Exception as e:
                logger.error(f"添加记忆时发生错误: {e}", exc_info=True)
                return f"添加记忆时发生错误: {str(e)}"

        @self.mcp.tool(
            name="memory_chat",
            description="与记忆系统对话"
        )
        async def memory_chat(message: str, user_id: str = None) -> str:
            """记忆对话"""
            try:
                if not user_id:
                    user_id = self.config.default_user_id

                logger.info(f"记忆对话: user_id={user_id}, message={message[:100]}...")

                # 调用MIRIX适配器进行对话
                chat_data = {
                    "message": message,
                    "user_id": user_id,
                    "use_memory": True
                }
                result = await self.mirix_adapter.chat_with_memory(chat_data)

                if result.get("success"):
                    response_data = result.get("response", {})
                    # 处理不同类型的响应数据
                    if isinstance(response_data, dict):
                        # 如果是字典，提取response字段
                        actual_response = response_data.get("response", response_data.get("message", ""))
                        if actual_response:
                            return str(actual_response)
                        else:
                            return str(response_data)
                    elif isinstance(response_data, str):
                        return response_data
                    else:
                        return str(response_data)
                else:
                    return f"对话失败: {result.get('error', '未知错误')}"

            except Exception as e:
                logger.error(f"记忆对话时发生错误: {e}", exc_info=True)
                return f"记忆对话时发生错误: {str(e)}"

        @self.mcp.tool(
            name="memory_search",
            description="搜索记忆内容"
        )
        async def memory_search(query: str, user_id: str = None, limit: int = 5) -> str:
            """搜索记忆"""
            try:
                if not user_id:
                    user_id = self.config.default_user_id

                logger.info(f"搜索记忆: user_id={user_id}, query={query}, limit={limit}")

                # 调用MIRIX适配器搜索记忆
                search_data = {
                    "query": query,
                    "user_id": user_id,
                    "limit": limit
                }
                result = await self.mirix_adapter.search_memory(search_data)

                if result.get("success"):
                    search_results = result.get("results", {})
                    # 从搜索结果中提取记忆内容
                    if isinstance(search_results, dict):
                        # 提取实际的搜索响应
                        actual_response = search_results.get("response", "")
                        if actual_response and "ERROR_RESPONSE_FAILED" not in actual_response:
                            return f"搜索结果:\n{actual_response}"
                        elif "ERROR_RESPONSE_FAILED" in str(search_results):
                            return "搜索出现错误，请稍后重试"
                        else:
                            return "未找到相关记忆"
                    elif isinstance(search_results, str):
                        if "ERROR_RESPONSE_FAILED" in search_results:
                            return "搜索出现错误，请稍后重试"
                        else:
                            return f"搜索结果:\n{search_results}"
                    else:
                        return "未找到相关记忆"
                else:
                    return f"搜索失败: {result.get('error', '未知错误')}"

            except Exception as e:
                logger.error(f"搜索记忆时发生错误: {e}", exc_info=True)
                return f"搜索记忆时发生错误: {str(e)}"

        @self.mcp.tool(
            name="memory_get_profile",
            description="获取用户记忆档案"
        )
        async def memory_get_profile(user_id: str = None) -> str:
            """获取用户档案"""
            try:
                if not user_id:
                    user_id = self.config.default_user_id

                logger.info(f"获取用户档案: user_id={user_id}")

                # 调用MIRIX适配器获取用户档案
                profile_data = {
                    "user_id": user_id,
                    "include_memories": True
                }
                result = await self.mirix_adapter.get_user_profile(profile_data)

                if result.get("success"):
                    profile_data = result.get("profile", {})
                    # 处理不同格式的档案数据
                    if isinstance(profile_data, dict) and "response" in profile_data:
                        # 如果包含实际的响应内容
                        actual_response = profile_data.get("response", "")
                        if actual_response:
                            return f"用户档案信息:\n{actual_response}"
                    
                    # 如果是标准格式的档案数据
                    if isinstance(profile_data, dict) and any(key in profile_data for key in ['user_id', 'memory_count']):
                        return f"用户档案:\n" + \
                               f"用户ID: {profile_data.get('user_id', user_id)}\n" + \
                               f"记忆数量: {profile_data.get('memory_count', 'N/A')}\n" + \
                               f"最后活动: {profile_data.get('last_activity', 'N/A')}"
                    
                    # 其他情况，直接返回内容
                    return f"用户档案:\n{str(profile_data)}"
                else:
                    return f"获取档案失败: {result.get('error', '未知错误')}"

            except Exception as e:
                logger.error(f"获取用户档案时发生错误: {e}", exc_info=True)
                return f"获取用户档案时发生错误: {str(e)}"
    
    async def run_sse(self):
        """运行 SSE MCP 服务器"""
        logger.info(f"启动 SSE MCP 服务器...")
        logger.info(f"监听地址: {self.config.sse_host}:{self.config.sse_port}")
        logger.info(f"服务端点: {self.config.sse_endpoint}")

        try:
            # 获取 FastMCP 的 Starlette 应用
            app = self.mcp.sse_app()

            logger.info("SSE MCP 服务器已启动，等待客户端连接...")
            logger.info(f"SSE连接端点: http://{self.config.sse_host}:{self.config.sse_port}{self.config.sse_endpoint}")

            # 使用uvicorn运行Starlette应用
            import uvicorn
            config = uvicorn.Config(
                app,
                host=self.config.sse_host,
                port=self.config.sse_port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()

        except Exception as e:
            logger.error(f"SSE 服务器运行失败: {e}")
            raise

    async def shutdown(self):
        """优雅关闭服务器"""
        logger.info("正在关闭 MCP 服务器...")
        # 这里可以添加清理逻辑
        logger.info("MCP 服务器已关闭")


# 便捷函数
async def create_mcp_server(config: MCPServerConfig) -> MCPServer:
    """创建 MCP 服务器实例
    
    Args:
        config: 服务器配置
        
    Returns:
        MCPServer: 服务器实例
    """
    return MCPServer(config)


async def run_mcp_server(config: MCPServerConfig) -> None:
    """运行 MCP 服务器
    
    Args:
        config: 服务器配置
    """
    server = await create_mcp_server(config)
    await server.run_sse()