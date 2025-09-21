#!/usr/bin/env python3
"""
MIRIX MCP 服务器 - 兼容版本

不依赖 MCP Python SDK 的简化实现，直接提供记忆管理功能。
可以通过 stdio 或 HTTP 接口使用。
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from config_simple import get_settings
from mirix_client_simple import MIRIXClient

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量
settings = get_settings()
mirix_client: Optional[MIRIXClient] = None


class MCPServer:
    """简化的 MCP 服务器实现"""

    def __init__(self):
        self.tools = {
            "memory_add": self.memory_add,
            "memory_search": self.memory_search,
            "memory_chat": self.memory_chat,
            "memory_get_profile": self.memory_get_profile,
        }

        self.resources = {
            "mirix://status": self.get_mirix_status,
            "mirix://memory/stats": self.get_memory_stats,
        }

    async def initialize(self):
        """初始化 MCP 服务器"""
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

    async def cleanup(self):
        """清理资源"""
        global mirix_client

        if mirix_client:
            await mirix_client.close()
            mirix_client = None

    async def memory_add(self, content: str, memory_type: str, context: Optional[str] = None) -> Dict[str, Any]:
        """添加记忆到 MIRIX 记忆系统"""
        if not mirix_client:
            return {"success": False, "error": "MIRIX client not initialized"}

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

    async def memory_search(self, query: str, memory_types: Optional[List[str]] = None, limit: int = 10) -> Dict[str, Any]:
        """在用户记忆系统中搜索相关信息"""
        if not mirix_client:
            return {"success": False, "error": "MIRIX client not initialized"}

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

    async def memory_chat(self, message: str, memorizing: bool = True, image_uris: Optional[List[str]] = None) -> Dict[str, Any]:
        """发送消息给 MIRIX Agent 并自动管理记忆"""
        if not mirix_client:
            return {"success": False, "error": "MIRIX client not initialized"}

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

    async def memory_get_profile(self, memory_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """获取用户的完整记忆档案概览"""
        if not mirix_client:
            return {"success": False, "error": "MIRIX client not initialized"}

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

    async def get_mirix_status(self) -> str:
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

    async def get_memory_stats(self) -> str:
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

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            if method == "initialize":
                # 初始化请求
                initialized = await self.initialize()
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {
                                "listChanged": True
                            },
                            "resources": {
                                "subscribe": True,
                                "listChanged": True
                            },
                            "prompts": {
                                "listChanged": True
                            },
                            "logging": {}
                        },
                        "serverInfo": {
                            "name": "MIRIX Memory Agent",
                            "version": "1.0.0"
                        }
                    }
                }

            elif method == "tools/list":
                # 列出可用工具
                tools = [
                    {
                        "name": "memory_add",
                        "description": "添加记忆到 MIRIX 记忆系统",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "content": {"type": "string", "description": "记忆内容"},
                                "memory_type": {"type": "string", "description": "记忆类型"},
                                "context": {"type": "string", "description": "上下文信息（可选）"}
                            },
                            "required": ["content", "memory_type"]
                        }
                    },
                    {
                        "name": "memory_search",
                        "description": "在用户记忆系统中搜索相关信息",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "搜索查询"},
                                "memory_types": {"type": "array", "items": {"type": "string"}, "description": "记忆类型（可选）"},
                                "limit": {"type": "integer", "description": "返回结果数量限制", "default": 10}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "memory_chat",
                        "description": "发送消息给 MIRIX Agent 并自动管理记忆",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string", "description": "聊天消息"},
                                "memorizing": {"type": "boolean", "description": "是否自动记忆", "default": True},
                                "image_uris": {"type": "array", "items": {"type": "string"}, "description": "图片 URI 列表（可选）"}
                            },
                            "required": ["message"]
                        }
                    },
                    {
                        "name": "memory_get_profile",
                        "description": "获取用户的完整记忆档案概览",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "memory_types": {"type": "array", "items": {"type": "string"}, "description": "要获取的记忆类型（可选）"}
                            },
                            "required": []
                        }
                    }
                ]

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": tools}
                }

            elif method == "tools/call":
                # 调用工具
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                if tool_name in self.tools:
                    result = await self.tools[tool_name](**arguments)

                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, indent=2, ensure_ascii=False)
                                }
                            ],
                            "isError": not result.get("success", True)
                        }
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool not found: {tool_name}"
                        }
                    }

            elif method == "resources/list":
                # 列出可用资源
                resources = [
                    {
                        "uri": "mirix://status",
                        "name": "MIRIX Status",
                        "description": "获取 MIRIX 后端状态信息",
                        "mimeType": "application/json"
                    },
                    {
                        "uri": "mirix://memory/stats",
                        "name": "Memory Statistics",
                        "description": "获取记忆系统统计信息",
                        "mimeType": "application/json"
                    }
                ]

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"resources": resources}
                }

            elif method == "resources/read":
                # 读取资源
                uri = params.get("uri")

                if uri in self.resources:
                    content = await self.resources[uri]()

                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "contents": [
                                {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "text": content
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Resource not found: {uri}"
                        }
                    }

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }


async def run_stdio_server():
    """运行 stdio MCP 服务器"""
    server = MCPServer()

    try:
        # 从 stdin 读取请求，向 stdout 发送响应
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                # 解析 JSON-RPC 请求
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    continue

                # 处理请求
                response = await server.handle_request(request)

                # 发送响应
                print(json.dumps(response, ensure_ascii=False), flush=True)

            except EOFError:
                break
            except Exception as e:
                logger.error(f"Error processing request: {e}")

    finally:
        await server.cleanup()


async def main():
    """主函数"""
    logger.info("Starting MIRIX MCP Server (Compatible Version)")
    logger.info(f"MIRIX Backend URL: {settings.mirix_backend_url}")
    logger.info(f"Default User ID: {settings.default_user_id}")

    try:
        await run_stdio_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())