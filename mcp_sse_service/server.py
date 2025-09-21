#!/usr/bin/env python3
"""
MIRIX MCP Server

基于官方 MCP Python SDK 的标准 MCP 服务器实现，提供记忆管理工具。
使用 FastMCP 框架简化开发和部署。
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, ImageContent

from config_simple import get_settings
from mirix_client_simple import MIRIXClient

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastMCP 服务器实例
mcp = FastMCP("MIRIX Memory Agent")

# 全局变量
settings = get_settings()
mirix_client: Optional[MIRIXClient] = None


async def initialize_mirix_client():
    """初始化 MIRIX 客户端连接"""
    global mirix_client

    mirix_client = MIRIXClient(
        base_url=settings.mirix_backend_url,
        timeout=settings.mirix_backend_timeout
    )

    try:
        await mirix_client.initialize()
        logger.info("Successfully connected to MIRIX backend")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to MIRIX backend: {e}")
        return False


async def cleanup_mirix_client():
    """清理 MIRIX 客户端连接"""
    global mirix_client

    if mirix_client:
        await mirix_client.close()
        mirix_client = None


# 记忆管理工具
@mcp.tool()
async def memory_add(
    content: str,
    memory_type: str,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    添加记忆到 MIRIX 记忆系统

    使用场景：
    - 用户分享个人信息、偏好或重要事实时使用
    - 学习新知识或技能时，将关键信息存储起来
    - 记录重要的对话内容或决定
    - 保存工作流程、步骤说明等程序性知识

    执行顺序：通常是对话中的第一步，在获取到有价值信息后立即使用
    预期效果：信息被永久存储，可通过 memory_search 检索，增强 AI 对用户的了解
    """
    if not mirix_client:
        return {
            "success": False,
            "error": "MIRIX client not initialized"
        }

    try:
        # 验证记忆类型
        valid_types = ["core", "episodic", "semantic", "procedural", "resource", "knowledge_vault"]
        if memory_type not in valid_types:
            return {
                "success": False,
                "error": f"Invalid memory_type. Must be one of: {', '.join(valid_types)}"
            }

        # 构建请求数据
        request_data = {
            "content": content,
            "memory_type": memory_type,
            "user_id": settings.default_user_id
        }

        if context:
            request_data["context"] = context

        # 调用 MIRIX 后端添加记忆
        result = await mirix_client.add_memory(request_data)

        logger.info(f"Memory added successfully: {memory_type}")

        return {
            "success": True,
            "message": "Memory added successfully",
            "memory_id": result.get("memory_id"),
            "memory_type": memory_type
        }

    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        return {
            "success": False,
            "error": f"Failed to add memory: {str(e)}"
        }


@mcp.tool()
async def memory_search(
    query: str,
    memory_types: Optional[List[str]] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    在用户记忆系统中搜索相关信息

    使用场景：
    - 用户询问之前讨论过的话题时使用
    - 需要回忆用户的偏好、习惯或个人信息时
    - 查找相关的知识、经验或程序步骤
    - 在回答问题前，先检索相关的背景信息

    执行顺序：通常在 memory_add 之前使用，避免重复存储；在回答用户问题前使用
    预期效果：获取相关的历史信息，提供更个性化、连贯的回应
    """
    if not mirix_client:
        return {
            "success": False,
            "error": "MIRIX client not initialized"
        }

    try:
        # 验证记忆类型（如果提供）
        if memory_types:
            valid_types = ["core", "episodic", "semantic", "procedural", "resource", "knowledge_vault"]
            invalid_types = [t for t in memory_types if t not in valid_types]
            if invalid_types:
                return {
                    "success": False,
                    "error": f"Invalid memory_types: {', '.join(invalid_types)}. Must be one of: {', '.join(valid_types)}"
                }

        # 构建搜索请求
        search_data = {
            "query": query,
            "user_id": settings.default_user_id,
            "limit": min(limit, 50)  # 限制最大返回数量
        }

        if memory_types:
            search_data["memory_types"] = memory_types

        # 调用 MIRIX 后端搜索记忆
        results = await mirix_client.search_memory(search_data)

        logger.info(f"Memory search completed: {query}")

        return {
            "success": True,
            "query": query,
            "memories": results.get("memories", []),
            "total_count": results.get("total_count", 0)
        }

    except Exception as e:
        logger.error(f"Failed to search memory: {e}")
        return {
            "success": False,
            "error": f"Failed to search memory: {str(e)}"
        }


@mcp.tool()
async def memory_chat(
    message: str,
    memorizing: bool = True,
    image_uris: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    发送消息给 MIRIX Agent 并自动管理记忆

    使用场景：
    - 进行需要记忆上下文的深度对话
    - 讨论重要话题，希望 AI 记住关键信息
    - 获取基于个人记忆的个性化回应
    - 当需要 AI 学习和适应用户偏好时

    执行顺序：可以独立使用，或在 memory_search 后使用以提供更好的上下文
    预期效果：获得个性化回应，重要信息自动存储到记忆中
    """
    if not mirix_client:
        return {
            "success": False,
            "error": "MIRIX client not initialized"
        }

    try:
        # 构建消息请求
        chat_data = {
            "message": message,
            "user_id": settings.default_user_id,
            "memorizing": memorizing,
            "model": settings.ai_model
        }

        if image_uris:
            chat_data["image_uris"] = image_uris

        # 调用 MIRIX 后端进行对话
        response = await mirix_client.send_chat_message(chat_data)

        logger.info(f"Memory chat completed: {len(message)} characters")

        return {
            "success": True,
            "response": response.get("response", ""),
            "memorized": response.get("memorized", False),
            "memory_updates": response.get("memory_updates", [])
        }

    except Exception as e:
        logger.error(f"Failed to process memory chat: {e}")
        return {
            "success": False,
            "error": f"Failed to process chat: {str(e)}"
        }


@mcp.tool()
async def memory_get_profile(
    memory_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    获取用户的完整记忆档案概览

    使用场景：
    - 初次与用户交互时，了解用户背景
    - 需要全面了解用户偏好和特点时
    - 为用户提供个性化建议前的信息收集
    - 定期回顾和更新对用户的了解

    执行顺序：通常在对话开始时使用，为后续交互提供基础
    预期效果：获得用户的全面画像，包括个人信息、偏好、历史记录等
    """
    if not mirix_client:
        return {
            "success": False,
            "error": "MIRIX client not initialized"
        }

    try:
        # 验证记忆类型（如果提供）
        if memory_types:
            valid_types = ["core", "episodic", "semantic", "procedural", "resource", "knowledge_vault"]
            invalid_types = [t for t in memory_types if t not in valid_types]
            if invalid_types:
                return {
                    "success": False,
                    "error": f"Invalid memory_types: {', '.join(invalid_types)}. Must be one of: {', '.join(valid_types)}"
                }

        # 构建档案请求
        profile_data = {
            "user_id": settings.default_user_id
        }

        if memory_types:
            profile_data["memory_types"] = memory_types

        # 调用 MIRIX 后端获取用户档案
        profile = await mirix_client.get_user_profile(profile_data)

        logger.info(f"User profile retrieved for user: {settings.default_user_id}")

        return {
            "success": True,
            "user_id": settings.default_user_id,
            "profile": profile.get("profile", {}),
            "memory_summary": profile.get("memory_summary", {}),
            "total_memories": profile.get("total_memories", 0),
            "last_updated": profile.get("last_updated")
        }

    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        return {
            "success": False,
            "error": f"Failed to get user profile: {str(e)}"
        }


# 资源定义
@mcp.resource("mirix://status")
async def mirix_status_resource() -> str:
    """获取 MIRIX 后端状态信息"""
    if not mirix_client:
        return json.dumps({
            "status": "disconnected",
            "error": "MIRIX client not initialized"
        }, indent=2)

    try:
        status = await mirix_client.get_mcp_status()
        return json.dumps(status, indent=2)
    except Exception as e:
        logger.error(f"Failed to get MIRIX status: {e}")
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)


@mcp.resource("mirix://memory/stats")
async def mirix_memory_stats_resource() -> str:
    """获取记忆系统统计信息"""
    if not mirix_client:
        return json.dumps({
            "error": "MIRIX client not initialized"
        }, indent=2)

    try:
        # 通过搜索空查询获取统计信息
        stats = await mirix_client.search_memory({
            "query": "",
            "user_id": settings.default_user_id,
            "limit": 0
        })
        return json.dumps(stats, indent=2)
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        return json.dumps({
            "error": str(e)
        }, indent=2)


# 提示定义
@mcp.prompt()
async def mirix_memory_prompt(
    context: str = "general",
    user_question: str = ""
) -> List[Dict[str, Any]]:
    """
    生成基于记忆上下文的系统提示

    Args:
        context: 对话上下文类型
        user_question: 用户问题（可选）
    """
    messages = [
        {
            "role": "system",
            "content": f"""You are MIRIX, an AI assistant with access to a sophisticated memory system.

Context: {context}

Available memory tools:
- memory_add: Store important information, preferences, and facts
- memory_search: Retrieve relevant memories to personalize responses
- memory_chat: Engage in memory-aware conversations
- memory_get_profile: Access comprehensive user profile

Guidelines:
1. Always search memories before responding to user questions
2. Use memories to provide personalized, contextual responses
3. Store important new information shared by the user
4. Reference specific memories when relevant to build continuity

Current user context: {settings.default_user_id}
"""
        }
    ]

    if user_question:
        messages.append({
            "role": "user",
            "content": user_question
        })

    return messages


async def main():
    """主函数 - 启动 MCP 服务器"""
    # 初始化 MIRIX 客户端
    if not await initialize_mirix_client():
        logger.error("Failed to initialize MIRIX client, exiting...")
        return

    try:
        # 运行 MCP 服务器
        logger.info("Starting MIRIX MCP Server...")
        await mcp.run(transport="stdio")
    finally:
        # 清理资源
        await cleanup_mirix_client()


if __name__ == "__main__":
    asyncio.run(main())