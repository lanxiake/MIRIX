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

        @self.mcp.tool()
        async def memory_add(content: str) -> str:
            """保存重要信息到用户记忆系统。

            用于长期记住用户偏好、重要事实或需要记录的内容。当用户明确表达想要记住某些信息，
            或当你发现重要的用户偏好、个人信息、重要决定等需要长期保存时使用此工具。

            适用场景：
                - 用户明确说"请记住..."或"帮我保存..."
                - 发现重要的用户偏好或个人信息
                - 用户做出重要决定或设定目标
                - 需要记录重要的对话要点或结论

            不适用场景：
                - 临时信息、一次性查询结果、通用知识

            Args:
                content (str): 要保存的重要信息内容。应该是清晰、完整的描述，包含足够的
                    上下文信息以便后续理解和检索。建议包含时间、背景等相关信息。

            Returns:
                str: 保存结果确认消息，包含成功或失败的详细信息。

            Example:
                >>> await memory_add("用户偏好使用Python进行Web开发，特别喜欢FastAPI框架")
                "成功添加记忆: 记忆已保存"
            """
            try:
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

        @self.mcp.tool()
        async def memory_chat(message: str) -> str:
            """基于用户记忆进行智能对话和复杂问题分析。

            适合需要推理、总结或综合分析的场景。这是一个智能分析工具，能够基于用户的
            历史记忆提供深度的、个性化的回答。

            使用时机：
                当用户的问题需要分析、推理、总结或综合多个记忆片段时使用。

            适用场景：
                - 复杂问题分析："基于我的学习经历，我应该如何规划职业发展？"
                - 个性化建议："根据我的偏好，推荐适合的技术栈"
                - 趋势总结："我最近的兴趣点有什么变化？"
                - 决策支持："考虑到我之前的经验，这个项目我应该注意什么？"
                - 深度对话：需要上下文理解和推理的对话

            工具选择指南：
                - 使用 memory_chat: 需要AI思考、分析、推理或提供建议时
                - 使用 memory_search: 只需要查找具体信息或事实时

            Args:
                message (str): 用户的问题或对话内容。可以是复杂的、需要分析的问题，
                    也可以是需要基于历史记忆进行个性化回答的查询。问题越具体和详细，
                    AI能提供的帮助就越精准。

            Returns:
                str: 基于用户记忆生成的智能回复，包含分析、建议或个性化的回答。

            Example:
                >>> await memory_chat("基于我之前学习的编程语言，我现在想学Web开发，你有什么建议？")
                "根据您之前提到喜欢Python，我建议您可以考虑Django或FastAPI框架..."
            """
            try:
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

        @self.mcp.tool()
        async def memory_search(
            query: str,
            memory_types: Optional[List[str]] = None,
            limit: int = 10
        ) -> str:
            """快速检索用户记忆中的特定信息（基于向量语义搜索）。

            使用先进的向量搜索技术，基于语义相似度而非关键字匹配来查找相关记忆。
            这种方法能够理解查询的语义含义，即使记忆中没有完全相同的关键词也能
            找到相关内容。

            使用时机：
                当需要查找用户之前提到的具体信息、偏好、事实或数据时使用。
                特别适合概念性搜索和语义相关的内容检索。

            适用场景：
                - 概念性查询："关于机器学习的内容" (即使记忆中用的是"AI"或"深度学习")
                - 语义相关搜索："编程相关的记忆" (能找到Python、JavaScript、算法等)
                - 情感或主题搜索："用户的兴趣爱好" (能理解各种表达方式)
                - 跨语言理解："travel memories" (能找到中文的"旅行"相关记忆)

            技术优势：
                - 语义理解：基于文本的语义含义而非字面匹配
                - 容错性强：拼写错误、同义词、相关概念都能被识别
                - 智能排序：按语义相似度自动排序结果
                - 跨领域搜索：能发现意想不到的相关连接

            工具选择指南：
                - 使用 memory_search: 语义搜索，理解概念和上下文，适合探索性查询
                - 使用 memory_chat: 复杂问题分析，需要推理、总结或综合多个信息

            Args:
                query (str): 搜索查询字符串。可以是概念、主题、问题或关键词。
                    支持自然语言查询，如"用户喜欢什么运动"、"编程学习资料"等。
                memory_types (Optional[List[str]], optional): 限制搜索的记忆类型。默认为 None（搜索所有类型）。
                    可选值：
                        - "core": 核心记忆（用户基本偏好、长期目标、重要个人信息）
                        - "episodic": 情景记忆（具体事件、对话片段、时间相关信息）
                        - "semantic": 语义记忆（知识、事实、概念、学习内容）
                        - "procedural": 程序记忆（技能、操作步骤、工作流程）
                        - "resource": 资源记忆（文档、文件、链接、外部资源）
                        - "credentials": 凭证记忆（敏感信息，内容会被掩码处理）
                limit (int, optional): 返回结果数量。默认为 10，范围 1-50。
                    建议根据查询复杂度调整：简单查询用5-10，复杂查询用15-30。

            Returns:
                str: 格式化的搜索结果，包含记忆类型标签、相似度分数和相关内容。
                    结果按语义相似度降序排列，每条记忆都包含相似度评分。
                    如果未找到结果，返回提示消息。

            Example:
                >>> await memory_search("用户的编程技能", memory_types=["semantic", "procedural"], limit=8)
                "找到 5 条相关记忆 (向量搜索):\\n\\n[semantic|0.92] Python编程语言掌握情况：熟练使用pandas和numpy..."
                
                >>> await memory_search("旅行经历", limit=6)
                "找到 3 条相关记忆 (向量搜索):\\n\\n[episodic|0.89] 上海之行：参观了外滩和东方明珠..."
            """
            try:
                user_id = self.config.default_user_id

                logger.info(f"搜索记忆: user_id={user_id}, query={query}, types={memory_types}, limit={limit}")

                # 使用新的向量搜索功能
                if memory_types:
                    # 验证记忆类型
                    valid_types = ["core", "episodic", "semantic", "procedural", "resource", "credentials"]
                    invalid_types = [t for t in memory_types if t not in valid_types]
                    if invalid_types:
                        return f"无效的记忆类型: {', '.join(invalid_types)}。支持的类型: {', '.join(valid_types)}"
                    
                    logger.debug(f"使用向量搜索指定类型: {memory_types}")
                    result = await self.mirix_adapter.search_memories_by_vector(
                        query=query,
                        memory_types=memory_types,
                        limit=limit,
                        user_id=user_id
                    )
                else:
                    # 搜索所有类型
                    all_types = ["core", "episodic", "semantic", "procedural", "resource", "credentials"]
                    logger.debug(f"使用向量搜索所有类型: {all_types}")
                    result = await self.mirix_adapter.search_memories_by_vector(
                        query=query,
                        memory_types=all_types,
                        limit=limit,
                        user_id=user_id
                    )

                if result.get("success"):
                    memories = result.get("all_memories", [])
                    search_results = result.get("results", {})
                    
                    if memories:
                        # 格式化多策略搜索结果，包含相似度分数和搜索方法
                        formatted_results = []
                        for memory in memories:
                            memory_type = memory.get("memory_type", "unknown")
                            similarity_score = memory.get("similarity_score", 0.0)
                            
                            # 获取该记忆类型使用的搜索方法
                            search_method_info = search_results.get(memory_type, {}).get("method", "unknown")
                            
                            # 获取内容，对于资源记忆优先返回完整内容
                            if memory_type == "resource":
                                # 资源记忆优先返回完整内容
                                content = (
                                    memory.get("content") or 
                                    memory.get("summary") or 
                                    memory.get("title") or
                                    memory.get("filename", "")
                                )
                            else:
                                # 其他记忆类型按原有逻辑
                                content = (
                                    memory.get("summary") or 
                                    memory.get("details") or 
                                    memory.get("content") or 
                                    memory.get("title") or 
                                    memory.get("name") or
                                    memory.get("key") or
                                    memory.get("caption") or
                                    memory.get("filename", "")
                                )
                            
                            if content:
                                # 对于资源记忆，返回更多内容；其他类型保持原有长度限制
                                if memory_type == "resource":
                                    # 资源记忆返回更多内容（前1000字符）
                                    content_preview = content[:1000] + ("..." if len(content) > 1000 else "")
                                else:
                                    # 其他记忆类型保持200字符限制
                                    content_preview = content[:200] + ("..." if len(content) > 200 else "")
                                
                                # 包含搜索方法信息
                                formatted_results.append(
                                    f"[{memory_type}|{similarity_score:.2f}|{search_method_info}] {content_preview}"
                                )
                        
                        if formatted_results:
                            search_method = result.get("search_method", "多策略搜索")
                            
                            # 添加搜索策略统计信息
                            method_stats = []
                            for mem_type, type_result in search_results.items():
                                if type_result.get("count", 0) > 0:
                                    method_stats.append(f"{mem_type}({type_result.get('method', 'unknown')}): {type_result.get('count', 0)}条")
                            
                            stats_info = " | ".join(method_stats) if method_stats else "无结果"
                            
                            return f"找到 {len(memories)} 条相关记忆 ({search_method}):\n搜索策略: {stats_info}\n\n" + "\n\n".join(formatted_results)
                        else:
                            return "未找到相关记忆内容"
                    else:
                        # 提供更详细的失败信息
                        failed_methods = []
                        for mem_type, type_result in search_results.items():
                            if type_result.get("count", 0) == 0:
                                error = type_result.get("error", "未知原因")
                                failed_methods.append(f"{mem_type}: {error}")
                        
                        if failed_methods:
                            return f"未找到相关记忆。详细信息:\n" + "\n".join(failed_methods)
                        else:
                            return "未找到相关记忆"
                else:
                    return f"搜索失败: {result.get('error', '未知错误')}"

            except Exception as e:
                logger.error(f"搜索记忆时发生错误: {e}", exc_info=True)
                return f"搜索记忆时发生错误: {str(e)}"

        @self.mcp.tool()
        async def resource_upload(
            file_name: str,
            file_content: str,
            file_type: Optional[str] = None,
            description: Optional[str] = None
        ) -> str:
            """上传文档文件到记忆系统，构建个人知识库。

            将文档内容转换为可搜索的知识库，支持多种文件格式。上传后的文档会被处理并
            集成到记忆系统中，可以通过其他工具进行搜索和查询。

            使用时机：
                当用户需要上传文档、建立知识库或保存重要文件内容时使用。

            适用场景：
                - 上传工作文档、学习资料或参考文件
                - 建立个人知识库和文档管理系统
                - 保存重要的PDF、Word、Excel等文件内容
                - 将外部文档集成到记忆系统中便于后续查询
                - 批量保存文本、代码或配置文件

            支持的文件类型：
                - 文本文档: .txt, .md, .rst
                - 办公文档: .pdf, .docx, .xlsx, .csv
                - 代码文件: .py, .js, .html, .css, .json, .xml
                - 配置文件: .yaml, .toml, .ini, .conf

            Args:
                file_name (str): 文件名，必须包含正确的扩展名以便系统识别文件类型。
                    建议使用描述性的文件名，便于后续管理和检索。
                file_content (str): 文件内容，可以是纯文本内容（适用于文本文件）或
                    Base64编码的二进制内容（适用于PDF、Office文档等）。
                    系统会自动检测并处理不同格式的内容。
                file_type (Optional[str], optional): 文件的MIME类型。默认为 None（自动推断）。
                    常用类型：
                        - "text/plain": 纯文本文件
                        - "text/markdown": Markdown文档
                        - "application/pdf": PDF文档
                        - "text/csv": CSV数据文件
                        - "application/json": JSON配置文件
                    如不提供，系统会根据文件名自动推断。
                description (Optional[str], optional): 文件描述。默认为 None。
                    建议包含文件的主要内容概述、来源或用途、重要的标签或分类信息。

            Returns:
                str: 上传结果详情，包含文档ID、文件大小和处理状态信息。

            Example:
                >>> await resource_upload(
                ...     "项目需求文档.md",
                ...     "# 项目需求\\n\\n## 功能列表...",
                ...     "text/markdown",
                ...     "Web项目的详细需求文档"
                ... )
                "文件上传成功!\\n文件名: 项目需求文档.md\\n文档ID: doc_123..."
            """
            try:
                user_id = self.config.default_user_id

                logger.info(f"上传资源: user_id={user_id}, file_name={file_name}, file_type={file_type}")

                # 调用MIRIX适配器上传文档
                upload_data = {
                    "file_name": file_name,
                    "content": file_content,  # 内容将在适配器中进行Base64编码处理
                    "file_type": file_type,
                    "description": description,
                    "user_id": user_id
                }
                result = await self.mirix_adapter.upload_document(upload_data)

                if result.get("success"):
                    file_info = result.get("file_info", {})
                    document_id = file_info.get("document_id", "")
                    content_size = file_info.get("content_size", 0)
                    
                    return f"文件上传成功!\n" + \
                           f"文件名: {file_name}\n" + \
                           f"文档ID: {document_id}\n" + \
                           f"文件大小: {content_size} 字节\n" + \
                           f"状态: 已处理并存储到资源记忆系统"
                else:
                    return f"文件上传失败: {result.get('error', '未知错误')}"

            except Exception as e:
                logger.error(f"上传资源时发生错误: {e}", exc_info=True)
                return f"上传资源时发生错误: {str(e)}"

    
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