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
            title="向记忆系统添加记忆",
            description="""向 MIRIX 记忆系统添加新的信息内容。

功能说明：
- 将用户提供的内容保存到记忆系统中
- 支持语义化存储，便于后续检索和对话

参数说明：
- content (str, 必需): 要添加到记忆中的文本内容，支持任意长度的文本
- user_id (str, 可选): 用户标识符，如果不提供则使用默认用户ID，默认不填写

返回值：
- 成功时返回确认消息，包含操作状态
- 失败时返回错误信息和具体原因

使用场景：
- 保存重要的对话内容或文档
- 记录用户偏好和个人信息
- 存储需要长期记忆的知识点
- 建立个人知识库"""
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
            title="使用自然语言与记忆系统对话获取记忆",
            description="""使用自然语言与 MIRIX 记忆系统进行智能对话交互。
功能说明：
- 基于用户的历史记忆进行上下文感知的对话
- 自动检索相关记忆内容来增强回答质量
- 支持多轮对话，保持对话连贯性
- 结合语义搜索和生成式AI提供智能回复

参数说明：
- message (str, 必需): 用户的对话消息或问题
- user_id (str, 可选): 用户标识符，用于获取对应的记忆上下文，默认不填写

返回值：
- 成功时返回AI生成的回复内容，基于用户记忆和当前问题
- 失败时返回错误信息和处理建议

使用场景：
- 询问之前保存的信息
- 基于历史记忆进行推理和分析
- 获得个性化的AI助手服务
- 进行知识问答和信息检索
- 延续之前的对话主题"""
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
            title="按记忆类型和关键词搜索记忆",
            description="""
            搜索记忆系统中的相关内容。
            此工具允许你根据关键字和指定的记忆类型在用户的记忆系统中检索信息。
            它会返回与查询最相关的记忆条目，并支持对不同类型记忆的筛选。
            Args:
                query (str): 必需。用于搜索记忆内容的关键字或短语，多个关键词，使用空格分隔。
                             例如: "用户喜欢的编程语言", "项目截止日期", "上次会议讨论的要点"
                memory_types (Optional[List[str]]): 可选。一个字符串列表，指定要搜索的记忆类型。
                                                     如果未提供，则会搜索所有支持的记忆类型。
                                                     支持的类型包括:
                                                     - "core": 核心记忆 (如用户基本偏好、长期目标)
                                                     - "episodic": 情景记忆 (如过去的事件、对话片段)
                                                     - "semantic": 语义记忆 (如知识、事实、概念)
                                                     - "procedural": 程序记忆 (如技能、操作步骤)
                                                     - "resource": 资源记忆 (如文档、文件、链接)
                                                     - "credentials": 凭证记忆 (如API密钥、敏感信息 - 但内容会被掩码)
                                                     例如: `["semantic", "resource"]`
                user_id (Optional[str]): 可选。指定要搜索哪个用户的记忆。如果未提供，将使用默认用户ID。
                limit (int): 可选。限制返回的记忆条目数量。默认为 10。最大值为 50。

            Returns:
                str: 格式化的搜索结果字符串。
                     如果找到相关记忆，会返回每个记忆的类型、摘要或内容片段。
                     如果未找到，则返回相应的提示信息。
                     如果参数无效或发生错误，会返回错误信息。

            Examples:
                1. 搜索关于“项目计划”的所有类型记忆:
                   `memory_search(query="项目计划")`

                2. 搜索“Python 语言”的语义记忆和程序记忆:
                   `memory_search(query="Python 语言", memory_types=["semantic", "procedural"])`

                3. 搜索“用户偏好”的核心记忆，并限制返回 3 条结果:
                   `memory_search(query="用户偏好", memory_types=["core"], limit=3)`
                   
                4. 多关键词搜索示例 - 搜索同时包含"电脑"和"水果"的记忆:
                   `memory_search(query="电脑 水果")`
            """


        )
        async def memory_search(
            query: str, 
            memory_types: Optional[List[str]] = None, 
            user_id: Optional[str] = None, 
            limit: int = 10
        ) -> str:
            """
            搜索记忆系统中的相关内容。
            
            此工具允许你根据关键字和指定的记忆类型在用户的记忆系统中检索信息。
            它会返回与查询最相关的记忆条目，并支持对不同类型记忆的筛选。

            Args:
                query (str): 必需。用于搜索记忆内容的关键字或短语，因为只使用了关键词搜索。
                             例如: "用户喜欢的编程语言", "项目截止日期", "上次会议讨论的要点"
                memory_types (Optional[List[str]]): 可选。一个字符串列表，指定要搜索的记忆类型。
                                                     如果未提供，则会搜索所有支持的记忆类型。
                                                     支持的类型包括:
                                                     - "core": 核心记忆 (如用户基本偏好、长期目标)
                                                     - "episodic": 情景记忆 (如过去的事件、对话片段)
                                                     - "semantic": 语义记忆 (如知识、事实、概念)
                                                     - "procedural": 程序记忆 (如技能、操作步骤)
                                                     - "resource": 资源记忆 (如文档、文件、链接)
                                                     - "credentials": 凭证记忆 (如API密钥、敏感信息 - 但内容会被掩码)
                                                     例如: `["semantic", "resource"]`
                user_id (Optional[str]): 可选。指定要搜索哪个用户的记忆。如果未提供，将使用默认用户ID。
                limit (int): 可选。限制返回的记忆条目数量。默认为 10。最大值为 50。

            Returns:
                str: 格式化的搜索结果字符串。
                     如果找到相关记忆，会返回每个记忆的类型、摘要或内容片段。
                     如果未找到，则返回相应的提示信息。
                     如果参数无效或发生错误，会返回错误信息。

            Examples:
                1. 搜索关于“项目计划”的所有类型记忆:
                   `memory_search(query="项目计划")`

                2. 搜索“Python 语言”的语义记忆和程序记忆:
                   `memory_search(query="Python 语言", memory_types=["semantic", "procedural"])`

                3. 搜索“用户偏好”的核心记忆，并限制返回 3 条结果:
                   `memory_search(query="用户偏好", memory_types=["core"], limit=3)`
                   
                4. 多关键词搜索示例 - 搜索同时包含"电脑"和"水果"的记忆:
                   `memory_search(query="电脑 水果")`
            """
            try:
                if not user_id:
                    user_id = self.config.default_user_id

                logger.info(f"搜索记忆: user_id={user_id}, query={query}, types={memory_types}, limit={limit}")

                # 使用新的分类搜索功能
                if memory_types:
                    # 验证记忆类型
                    valid_types = ["core", "episodic", "semantic", "procedural", "resource", "credentials"]
                    invalid_types = [t for t in memory_types if t not in valid_types]
                    if invalid_types:
                        return f"无效的记忆类型: {', '.join(invalid_types)}。支持的类型: {', '.join(valid_types)}"
                    
                    result = await self.mirix_adapter.search_memories_by_types(
                        query=query,
                        memory_types=memory_types,
                        limit=limit,
                        user_id=user_id
                    )
                else:
                    # 搜索所有类型
                    all_types = ["core", "episodic", "semantic", "procedural", "resource", "credentials"]
                    result = await self.mirix_adapter.search_memories_by_types(
                        query=query,
                        memory_types=all_types,
                        limit=limit,
                        user_id=user_id
                    )

                if result.get("success"):
                    memories = result.get("all_memories", [])
                    if memories:
                        # 格式化搜索结果
                        formatted_results = []
                        for memory in memories:
                            memory_type = memory.get("memory_type", "unknown")
                            content = memory.get("summary") or memory.get("details") or memory.get("content") or memory.get("title") or memory.get("filename", "")
                            if content:
                                formatted_results.append(f"[{memory_type}] {content[:200]}...")
                        
                        if formatted_results:
                            return f"找到 {len(memories)} 条相关记忆:\n\n" + "\n\n".join(formatted_results)
                        else:
                            return "未找到相关记忆内容"
                    else:
                        return "未找到相关记忆"
                else:
                    return f"搜索失败: {result.get('error', '未知错误')}"

            except Exception as e:
                logger.error(f"搜索记忆时发生错误: {e}", exc_info=True)
                return f"搜索记忆时发生错误: {str(e)}"

        @self.mcp.tool(
            name="resource_upload",
            description=  """
            上传文档或文件到 MIRIX 资源记忆系统。
            
            此工具允许你将各种格式的文档（如文本、Markdown、Excel、CSV、PDF等）上传到资源记忆系统。
            系统会自动检测文件类型并进行处理。文件内容可以是纯文本或 Base64 编码的字符串。

            Args:
                file_name (str): 必需。要上传的文件名，包括文件扩展名（例如: `report.pdf`, `data.csv`, `notes.md`）。
                                 扩展名有助于系统准确识别文件类型。
                file_content (str): 必需。文件内容的字符串表示。可以是文件的原始文本内容，
                                    也可以是 Base64 编码的二进制内容（工具会自动检测并解码）。
                file_type (Optional[str]): 可选。文件的 MIME 类型（例如: `application/pdf`, `text/csv`, `text/markdown`）。
                                           如果提供，将优先使用此类型；否则，工具会尝试从文件名或内容自动推断。
                                           支持的类型包括但不限于: `text/plain`, `text/markdown`, `text/csv`,
                                           `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`,
                                           `application/json`, `application/xml`, `text/html`, `application/pdf`。
                description (Optional[str]): 可选。对文件内容的简短描述，帮助更好地理解和检索文件。
                                            例如: "2023年第四季度销售报告", "项目需求规格书V1.0"。
                user_id (Optional[str]): 可选。指定此资源所属的用户ID。如果未提供，将使用默认用户ID。

            Returns:
                str: 包含上传结果的格式化字符串。成功时会返回文件名、文档ID、文件大小和处理状态；
                     失败时会返回详细的错误信息。

            Examples:
                1. 上传一份简单的 Markdown 文档:
                   `resource_upload(file_name="meeting_notes.md", file_content="# 会议纪要\n\n讨论了项目进展和下一步计划。")`

                2. 上传 Base64 编码的 CSV 文件（假设 `base64_csv_content` 是 Base64 字符串）:
                   `resource_upload(file_name="users.csv", file_content=base64_csv_content, file_type="text/csv", description="导出用户数据")`

                3. 上传一个 PDF 文件（需要将PDF内容转换为Base64字符串）:
                   `resource_upload(file_name="report.pdf", file_content=base64_pdf_content, file_type="application/pdf")`
            """
        )
        async def resource_upload(
            file_name: str,
            file_content: str,
            file_type: Optional[str] = None,
            description: Optional[str] = None,
            user_id: Optional[str] = None
        ) -> str:
            """
            上传文档或文件到 MIRIX 资源记忆系统。
            
            此工具允许你将各种格式的文档（如文本、Markdown、Excel、CSV、PDF等）上传到资源记忆系统。
            系统会自动检测文件类型并进行处理。文件内容可以是纯文本或 Base64 编码的字符串。

            Args:
                file_name (str): 必需。要上传的文件名，包括文件扩展名（例如: `report.pdf`, `data.csv`, `notes.md`）。
                                 扩展名有助于系统准确识别文件类型。
                file_content (str): 必需。文件内容的字符串表示。可以是文件的原始文本内容，
                                    也可以是 Base64 编码的二进制内容（工具会自动检测并解码）。
                file_type (Optional[str]): 必需。文件的 MIME 类型（例如: `application/pdf`, `text/csv`, `text/markdown`）。
                                           如果提供，将优先使用此类型；否则，工具会尝试从文件名或内容自动推断。
                                           支持的类型包括但不限于: `text/plain`, `text/markdown`, `text/csv`,
                                           `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`,
                                           `application/json`, `application/xml`, `text/html`, `application/pdf`。
                description (Optional[str]): 可选。对文件内容的简短描述，帮助更好地理解和检索文件。
                                            例如: "2023年第四季度销售报告", "项目需求规格书V1.0"。
                user_id (Optional[str]): 可选。指定此资源所属的用户ID。如果未提供，将使用默认用户ID。

            Returns:
                str: 包含上传结果的格式化字符串。成功时会返回文件名、文档ID、文件大小和处理状态；
                     失败时会返回详细的错误信息。

            Examples:
                1. 上传一份简单的 Markdown 文档:
                   `resource_upload(file_name="meeting_notes.md", file_content="# 会议纪要\n\n讨论了项目进展和下一步计划。")`

                2. 上传 Base64 编码的 CSV 文件（假设 `base64_csv_content` 是 Base64 字符串）:
                   `resource_upload(file_name="users.csv", file_content=base64_csv_content, file_type="text/csv", description="导出用户数据")`

                3. 上传一个 PDF 文件（需要将PDF内容转换为Base64字符串）:
                   `resource_upload(file_name="report.pdf", file_content=base64_pdf_content, file_type="application/pdf")`
            """
            try:
                if not user_id:
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