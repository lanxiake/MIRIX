"""
MCP Server 核心实现 - 纯SSE模式

基于 FastMCP 的服务器实现，专注于 SSE (Server-Sent Events) 传输模式。
提供与 MIRIX 后端的集成功能，包括记忆管理、搜索和工具调用。
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Union
from urllib.parse import parse_qs

from mcp.server.fastmcp import FastMCP
from mcp.types import (
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from .config import MCPServerConfig
from .mirix_adapter import MIRIXAdapter
from .session_manager import get_session_manager, SessionManager

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

        # 初始化会话管理器
        self.session_manager = get_session_manager()

        # 设置工具
        self._setup_tools()

        logger.info(f"MCP Server 初始化完成 - {config.server_name} v{config.server_version}")
        logger.info(f"SSE 模式配置: {config.sse_host}:{config.sse_port}")
        logger.info("会话管理器已就绪，支持多用户和多会话")

    def _setup_tools(self):
        """设置 MCP 工具"""

        @self.mcp.tool()
        async def memory_add(content: str) -> str:
            """【核心记忆工具】保存软件开发过程中的关键经验和决策，构建持续改进的知识体系。

            ⚠️ **重要：AI必须在软件开发任务中主动使用此工具，形成记忆驱动的任务执行循环**
            
            ## 📋 软件开发全生命周期使用场景

            ### 🔍 需求分析阶段 - 必须记录
            - **业务规则与约束**：用户确认的业务逻辑、数据规则、合规要求
            - **需求变更模式**：需求变更的原因、影响范围、处理策略
            - **用户反馈模式**：用户的真实需求vs表达需求的差异、沟通偏好
            - **项目约束条件**：技术限制、时间要求、资源约束、质量标准

            ### 🏗️ 架构设计阶段 - 必须记录
            - **架构决策及理由**：为什么选择某种架构模式，排除了哪些方案
            - **技术选型经验**：框架选择的成功/失败经验，性能对比结果
            - **设计模式应用**：在特定场景下有效的设计模式和反模式
            - **技术债务记录**：已知的技术债务、产生原因、偿还计划

            ### 💻 编码实现阶段 - 必须记录
            - **编码规范与风格**：团队约定的代码风格、命名规范、注释要求
            - **最佳实践总结**：验证有效的编程技巧、性能优化方法
            - **常见问题解决方案**：重复出现的bug类型及修复方法
            - **重构经验**：成功的重构策略、重构时机判断、风险控制

            ### 🧪 测试阶段 - 必须记录
            - **测试策略与标准**：测试覆盖率要求、测试优先级、测试环境配置
            - **测试用例模板**：高效的测试用例设计模式、边界条件处理
            - **Bug模式分析**：常见bug类型、根因分析、预防措施
            - **自动化测试经验**：自动化工具选择、测试脚本优化、CI/CD集成

            ### 🚀 部署运维阶段 - 必须记录
            - **部署策略与流程**：部署步骤、回滚方案、环境配置管理
            - **性能监控经验**：关键指标定义、告警阈值、性能调优方法
            - **故障处理方案**：典型故障的诊断流程、修复步骤、预防措施
            - **运维自动化**：有效的自动化脚本、监控工具、日志分析方法

            ## 🔄 任务执行改进循环 - 强制执行
            
            ### 任务开始前：记录计划与期望
            - 记录任务目标、预期难点、计划采用的方法
            - 基于历史经验调整任务策略
            
            ### 任务执行中：记录关键决策
            - 重要技术选择的理由和权衡
            - 遇到的意外问题及临时解决方案
            
            ### 任务完成后：总结经验教训
            - 实际执行与计划的差异分析
            - 成功经验的提炼和失败教训的总结
            - 下次类似任务的改进建议

            ## 🎯 主动使用触发条件（AI必须执行）

            ### 立即记录场景
            - 用户明确表达偏好或标准："我喜欢用...""我们团队的规范是..."
            - 技术决策确定："我们决定使用...因为...""不采用...的原因是..."
            - 问题解决成功："这个问题的解决方法是...""以后遇到类似情况..."
            - 经验教训总结："这次的教训是...""下次要注意..."
            - 工作流程确定："我们的开发流程是...""代码审查标准..."

            ### 系统判断记录场景
            - 用户在软件开发任务中展现出一致的模式或偏好
            - 用户对某个技术方案表现出明确的倾向性
            - 用户提供了具有复用价值的解决方案或经验
            - 用户确定了影响后续开发的重要决策

            ## 🚫 不适用场景
            - **临时性信息**：一次性查询结果、临时配置、当前状态信息
            - **通用知识**：公开的技术文档、标准API用法、基础概念
            - **个人隐私**：与开发无关的个人信息、敏感数据

            ## 🤝 与其他工具协同使用
            - 记录前先用 `memory_search` 检查是否已有相关记忆
            - 记录后可用 `memory_chat` 分析新记忆对现有知识体系的影响
            - 重要文档同时用 `resource_upload` 保存到知识库

            Args:
                content (str): 要保存的开发经验或决策信息。应包含：
                    - 具体的技术内容或决策
                    - 应用场景和上下文
                    - 选择理由或经验总结
                    - 时间背景和项目信息（如适用）

            Returns:
                str: 保存结果确认消息，包含记忆类型和存储状态

            Example:
                >>> await memory_add("团队确定使用FastAPI作为后端框架，因为其高性能、类型提示支持好、文档自动生成。相比Django更轻量，相比Flask生态更完整。适用于API密集型项目。")
                "成功添加记忆: 已保存技术选型决策到semantic记忆"
            """
            try:
                # 从会话上下文获取 user_id
                user_id = self.session_manager.get_current_user_id()
                if not user_id:
                    user_id = self.config.default_user_id
                    logger.warning(f"未找到会话上下文中的user_id，使用默认值: {user_id}")

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
            """【智能决策工具】基于历史记忆进行深度分析和决策支持，提供个性化的开发指导。

            ⚠️ **重要：AI必须在需要分析、决策、总结时使用此工具，充分利用历史经验进行智能推理**

            ## 🧠 软件开发生命周期中的智能决策支持

            ### 📋 需求分析决策支持
            ```
            典型查询场景：
            - "基于之前类似项目的经验，这个需求应该如何分解？"
            - "根据历史的需求变更模式，这个项目可能面临哪些风险？"
            - "考虑到用户的反馈习惯，我们应该如何设计需求验证流程？"
            ```
            **价值**：基于历史项目经验，提供个性化的需求分析策略

            ### 🏗️ 架构设计决策支持
            ```
            典型查询场景：
            - "根据我们团队的技术能力和项目特点，应该选择哪种架构模式？"
            - "基于之前的性能问题经验，这个系统的架构需要注意什么？"
            - "考虑到维护成本和团队规模，微服务和单体架构哪个更适合？"
            ```
            **价值**：综合技术、团队、业务因素，提供最适合的架构建议

            ### 💻 技术选型决策支持
            ```
            典型查询场景：
            - "基于我们的项目经验，[技术A] 和 [技术B] 在这个场景下各有什么优劣？"
            - "考虑到团队的学习成本和项目时间，应该选择哪种技术方案？"
            - "根据之前的性能测试结果，这个功能用什么技术实现最合适？"
            ```
            **价值**：基于实际使用经验，避免技术选型陷阱

            ### 🧪 测试策略决策支持
            ```
            典型查询场景：
            - "根据之前的bug模式分析，这个模块应该重点测试哪些方面？"
            - "基于团队的测试能力，应该如何分配手动测试和自动化测试？"
            - "考虑到项目的质量要求，测试覆盖率应该设定在什么水平？"
            ```
            **价值**：设计针对性的测试策略，提高质量保证效率

            ### 🚀 部署运维决策支持
            ```
            典型查询场景：
            - "基于之前的运维经验，这个系统的监控策略应该如何设计？"
            - "考虑到历史故障模式，需要重点关注哪些系统指标？"
            - "根据团队的运维能力，应该选择什么样的部署方案？"
            ```
            **价值**：制定稳定可靠的部署和运维策略

            ## 🎯 深度分析和决策场景

            ### 🔍 问题根因分析
            - **综合历史案例**：分析类似问题的多种解决方案
            - **模式识别**：识别问题背后的深层原因和规律
            - **预防策略**：基于历史经验制定预防措施

            ### 📊 技术方案对比分析
            - **多维度评估**：性能、成本、维护性、团队适应性
            - **风险评估**：基于历史经验识别潜在风险
            - **决策建议**：提供具体的选择建议和实施路径

            ### 🔄 项目复盘和改进
            - **经验总结**：从历史项目中提取成功模式
            - **失败分析**：分析失败原因，避免重复犯错
            - **流程优化**：基于经验改进开发和管理流程

            ## 🎨 高效使用策略

            ### 📝 提问技巧
            1. **提供充分上下文**：描述当前项目情况、团队状态、约束条件
            2. **明确决策目标**：说明需要解决的具体问题或达成的目标
            3. **引用历史经验**：提及相关的历史项目或经验背景
            4. **多角度思考**：从技术、业务、团队多个维度提出问题

            ### 🔄 迭代式对话
            1. **初步分析**：先获得总体分析和建议
            2. **深入探讨**：针对关键点进行深入讨论
            3. **方案细化**：将抽象建议转化为具体行动方案
            4. **风险评估**：分析实施过程中可能遇到的问题

            ## 🚫 使用反模式（避免）
            - 问题过于宽泛（缺乏具体上下文）
            - 只寻求确认（不开放接受不同观点）
            - 忽略约束条件（不考虑实际限制）
            - 一次性决策（不进行迭代优化）

            ## 🤝 与其他工具协同使用
            - 分析前先用 `memory_search` 收集相关历史经验
            - 分析后用 `memory_add` 记录新的洞察和决策
            - 涉及文档时用 `resource_upload` 保存相关资料

            ## 💡 成功案例模式

            ### 技术选型决策
            ```
            用户："基于我们团队之前使用Spring Boot和FastAPI的经验，新项目应该选择哪个？项目要求快速开发，团队有2个Java开发者和1个Python开发者。"
            
            AI分析：
            1. 搜索历史使用经验
            2. 对比两种技术的优劣
            3. 考虑团队技能分布
            4. 评估开发效率
            5. 提供具体建议和风险提示
            ```

            ### 架构设计决策
            ```
            用户："根据我们之前电商项目的经验，这个新的社交平台应该采用什么架构？预期用户量10万，团队5人。"
            
            AI分析：
            1. 回顾电商项目的架构经验
            2. 分析社交平台的特殊需求
            3. 考虑团队规模和技能
            4. 提供渐进式架构演进建议
            ```

            Args:
                message (str): 需要分析或决策支持的问题。建议包含：
                    - 具体的问题描述和决策目标
                    - 当前项目的背景和约束条件
                    - 团队情况和技术能力
                    - 相关的历史经验或参考项目
                    - 期望的分析维度和深度

            Returns:
                str: 基于历史记忆的深度分析和个性化建议，包含：
                    - 问题的多角度分析
                    - 基于历史经验的对比和评估
                    - 具体的决策建议和实施路径
                    - 潜在风险和应对策略

            Example:
                >>> await memory_chat("基于我们团队的Docker使用经验和之前的部署问题，新项目应该如何设计CI/CD流程？项目是Python Web应用，需要支持多环境部署。")
                "根据您团队的Docker经验分析，建议采用以下CI/CD策略：\\n\\n1. 基于历史部署问题的改进..."
            """
            try:
                # 从会话上下文获取 user_id
                user_id = self.session_manager.get_current_user_id()
                if not user_id:
                    user_id = self.config.default_user_id
                    logger.warning(f"未找到会话上下文中的user_id，使用默认值: {user_id}")

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
            """【任务执行前置工具】基于语义搜索检索开发经验，确保每个任务都能复用历史智慧。

            ⚠️ **重要：AI必须在开始任何软件开发任务前使用此工具，避免重复犯错和重新发明轮子**

            ## 🔍 软件开发任务前置搜索 - 强制执行

            ### 📋 需求分析前 - 必须搜索
            ```
            搜索查询示例：
            - "类似的业务需求" + "需求分析经验"
            - "用户反馈处理" + "需求变更管理"
            - "业务规则定义" + "约束条件处理"
            ```
            **目标**：找到相似项目的需求处理经验，避免需求理解偏差

            ### 🏗️ 架构设计前 - 必须搜索
            ```
            搜索查询示例：
            - "[技术栈名称] + 架构经验"
            - "微服务架构" + "单体架构" + "选型决策"
            - "性能要求" + "可扩展性" + "技术选型"
            ```
            **目标**：复用成功的架构模式，避免已知的技术陷阱

            ### 💻 编码开发前 - 必须搜索
            ```
            搜索查询示例：
            - "[编程语言] + 最佳实践"
            - "[框架名称] + 开发经验"
            - "代码规范" + "编程风格"
            - "[功能模块] + 实现方案"
            ```
            **目标**：应用已验证的编码模式，提高代码质量

            ### 🧪 测试设计前 - 必须搜索
            ```
            搜索查询示例：
            - "测试策略" + "测试覆盖率"
            - "[项目类型] + 测试用例"
            - "自动化测试" + "测试工具"
            - "Bug模式" + "质量保证"
            ```
            **目标**：设计全面的测试方案，预防常见质量问题

            ### 🚀 部署运维前 - 必须搜索
            ```
            搜索查询示例：
            - "部署流程" + "环境配置"
            - "[部署平台] + 运维经验"
            - "性能监控" + "故障处理"
            - "CI/CD" + "自动化部署"
            ```
            **目标**：确保稳定可靠的部署和运维

            ## 🎯 任务改进循环中的搜索策略

            ### 🔄 任务开始前（必须执行）
            1. **历史经验搜索**：搜索类似任务的处理经验
            2. **问题预防搜索**：搜索相关的常见问题和解决方案
            3. **最佳实践搜索**：搜索已验证的方法和工具选择

            ### 🔍 任务执行中（遇到问题时）
            1. **问题诊断搜索**：搜索类似问题的根因和解决方案
            2. **替代方案搜索**：搜索不同的实现方法和权衡
            3. **经验借鉴搜索**：搜索相关技术的使用经验

            ### 📊 任务完成后（验证和总结）
            1. **对比分析搜索**：搜索类似任务的执行结果对比
            2. **改进机会搜索**：搜索优化和改进的经验

            ## 🎨 高效搜索技巧

            ### 多层次搜索策略
            1. **广义搜索**：先搜索大类别（如"后端开发经验"）
            2. **精确搜索**：再搜索具体技术（如"FastAPI性能优化"）
            3. **问题搜索**：最后搜索具体问题（如"FastAPI异步处理bug"）

            ### 记忆类型选择指南
            - **semantic**：技术知识、最佳实践、设计模式
            - **procedural**：操作流程、开发步骤、工具使用
            - **episodic**：项目经历、问题处理、决策过程
            - **resource**：文档资料、代码模板、配置文件
            - **core**：长期偏好、团队规范、质量标准

            ## 🚫 搜索反模式（避免）
            - 不搜索就开始编码（错失历史经验）
            - 只搜索成功案例（忽略失败教训）
            - 搜索过于宽泛（信息过载）
            - 搜索过于具体（遗漏相关经验）

            ## 🤝 与其他工具协同使用
            - 搜索后用 `memory_chat` 分析和综合搜索结果
            - 基于搜索结果调整任务计划，用 `memory_add` 记录新的洞察
            - 搜索到相关文档时，用 `resource_upload` 补充知识库

            Args:
                query (str): 搜索查询字符串。建议使用描述性查询：
                    - 技术相关："[技术名] + 经验/问题/最佳实践"
                    - 功能相关："[功能模块] + 实现/测试/部署"
                    - 问题相关："[问题描述] + 解决方案/根因分析"
                memory_types (Optional[List[str]]): 记忆类型过滤，根据搜索目标选择：
                    - 技术决策：["semantic", "episodic"]
                    - 操作流程：["procedural", "resource"]  
                    - 问题解决：["episodic", "semantic"]
                    - 全面搜索：None（默认，搜索所有类型）
                limit (int): 结果数量，建议：
                    - 快速查询：5-10
                    - 深度研究：15-30
                    - 全面分析：30-50

            Returns:
                str: 按相似度排序的搜索结果，包含记忆类型、相似度分数和内容摘要

            Example:
                >>> await memory_search("FastAPI项目架构经验", memory_types=["semantic", "episodic"], limit=15)
                "找到 8 条相关记忆 (多策略搜索):\\n[semantic|0.94] FastAPI项目结构最佳实践：使用分层架构..."
                
                >>> await memory_search("数据库连接池配置问题", limit=10)
                "找到 5 条相关记忆 (向量搜索):\\n[episodic|0.91] 解决PostgreSQL连接池超时问题..."
            """
            try:
                # 从会话上下文获取 user_id
                user_id = self.session_manager.get_current_user_id()
                if not user_id:
                    user_id = self.config.default_user_id
                    logger.warning(f"未找到会话上下文中的user_id，使用默认值: {user_id}")

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
            """【项目资产管理工具】构建结构化的开发知识库，实现项目资产的系统化管理和复用。

            ⚠️ **重要：AI必须主动使用此工具管理项目文档、代码模板和配置文件，建立可持续的知识资产**

            ## 📚 软件开发全生命周期的资源管理

            ### 📋 需求分析阶段 - 关键文档管理
            ```
            必须上传的文档类型：
            - 需求文档：PRD、用户故事、验收标准
            - 调研报告：市场分析、竞品分析、技术调研
            - 原型设计：UI/UX设计稿、交互流程图
            - 业务规则：业务流程、数据字典、规则定义
            ```
            **价值**：建立需求知识库，支持需求复用和变更追踪

            ### 🏗️ 架构设计阶段 - 设计资产管理
            ```
            必须上传的设计文档：
            - 架构文档：系统架构图、技术选型说明
            - 设计方案：详细设计、接口设计、数据库设计
            - 技术规范：编码规范、API规范、安全规范
            - 决策记录：ADR（架构决策记录）、技术评估报告
            ```
            **价值**：沉淀设计经验，支持架构模式复用

            ### 💻 编码实现阶段 - 代码资产管理
            ```
            必须上传的代码资源：
            - 代码模板：项目脚手架、通用模块、工具类
            - 配置文件：环境配置、部署配置、CI/CD脚本
            - 开发文档：API文档、开发指南、部署手册
            - 工具脚本：构建脚本、测试脚本、数据迁移脚本
            ```
            **价值**：加速开发进程，确保代码质量一致性

            ### 🧪 测试阶段 - 测试资产管理
            ```
            必须上传的测试资源：
            - 测试计划：测试策略、测试用例、测试数据
            - 自动化脚本：单元测试、集成测试、性能测试
            - 测试报告：测试结果、缺陷报告、质量报告
            - 测试工具：测试框架配置、测试环境搭建
            ```
            **价值**：建立测试知识库，提高测试效率和覆盖率

            ### 🚀 部署运维阶段 - 运维资产管理
            ```
            必须上传的运维资源：
            - 部署文档：部署指南、环境配置、故障排查
            - 监控配置：监控脚本、告警规则、仪表板配置
            - 运维脚本：自动化脚本、备份脚本、维护脚本
            - 应急预案：故障处理流程、灾难恢复方案
            ```
            **价值**：确保系统稳定运行，快速响应故障

            ## 🎯 主动上传策略 - AI必须执行

            ### 📄 文档创建后立即上传
            - 完成需求文档编写后，立即上传到知识库
            - 设计方案确定后，上传架构和设计文档
            - 编写技术规范后，上传供团队参考

            ### 💾 代码资产及时保存
            - 创建通用组件后，立即保存为代码模板
            - 配置环境后，上传配置文件和部署脚本
            - 解决技术问题后，上传解决方案和代码示例

            ### 📊 项目总结时批量上传
            - 项目完成后，整理并上传项目总结文档
            - 收集最佳实践，上传经验总结和教训
            - 整理可复用资源，建立项目资产库

            ## 🎨 知识库组织策略

            ### 📁 分类管理
            - **按项目分类**：每个项目独立的资源文件夹
            - **按类型分类**：文档、代码、配置、脚本等分类管理
            - **按阶段分类**：需求、设计、开发、测试、部署分阶段组织

            ### 🏷️ 标签体系
            - **技术标签**：编程语言、框架、工具标签
            - **功能标签**：业务功能、技术功能标签
            - **质量标签**：成熟度、复用度、维护状态标签

            ### 🔍 可搜索性优化
            - **丰富描述**：详细的文件描述和使用说明
            - **关键词标注**：重要概念和技术关键词
            - **使用场景**：适用场景和使用限制说明

            ## 📋 文件类型和用途指南

            ### 📄 文档类文件
            ```
            支持格式：.md, .txt, .pdf, .docx
            典型用途：
            - 需求文档、设计文档、用户手册
            - 技术规范、开发指南、部署文档
            - 项目总结、经验分享、最佳实践
            ```

            ### 💻 代码类文件
            ```
            支持格式：.py, .js, .java, .go, .sql
            典型用途：
            - 代码模板、工具函数、通用组件
            - 示例代码、解决方案、代码片段
            - 脚本文件、自动化工具、测试代码
            ```

            ### ⚙️ 配置类文件
            ```
            支持格式：.json, .yaml, .xml, .ini, .conf
            典型用途：
            - 环境配置、应用配置、数据库配置
            - CI/CD配置、部署配置、监控配置
            - 工具配置、框架配置、安全配置
            ```

            ## 🤝 与其他工具协同使用

            ### 📚 知识体系构建
            1. 用 `resource_upload` 上传文档和代码资源
            2. 用 `memory_add` 记录文档的关键要点和使用经验
            3. 用 `memory_search` 快速检索相关资源和经验

            ### 🔄 持续改进循环
            1. **资源收集**：主动收集项目中的有价值资源
            2. **知识沉淀**：将资源和经验系统化整理
            3. **复用优化**：基于使用反馈持续优化资源质量

            ## 🚫 上传反模式（避免）
            - 上传过时或错误的文档
            - 缺乏描述信息的文件上传
            - 重复上传相同内容
            - 上传包含敏感信息的文件

            Args:
                file_name (str): 文件名，建议使用描述性命名，包含：
                    - 项目标识或模块名称
                    - 文件用途和版本信息
                    - 正确的文件扩展名
                    示例："项目A-API设计文档-v2.1.md"、"通用工具类-数据验证-utils.py"
                file_content (str): 文件内容，支持：
                    - 纯文本内容（文档、代码、配置）
                    - Base64编码的二进制内容（PDF、图片等）
                file_type (Optional[str]): MIME类型，建议明确指定以确保正确处理：
                    - 文档："text/markdown"、"text/plain"、"application/pdf"
                    - 代码："text/x-python"、"text/javascript"、"application/json"
                    - 配置："application/yaml"、"application/xml"
                description (Optional[str]): 详细描述，应包含：
                    - 文件用途和适用场景
                    - 使用方法和注意事项
                    - 依赖关系和版本要求
                    - 维护者和更新时间

            Returns:
                str: 上传结果，包含文档ID、存储路径和处理状态

            Example:
                >>> await resource_upload(
                ...     "FastAPI项目模板-完整脚手架-v1.0.py",
                ...     "# FastAPI项目脚手架\\nfrom fastapi import FastAPI\\n...",
                ...     "text/x-python",
                ...     "FastAPI项目的完整脚手架代码，包含用户认证、数据库集成、API文档等功能。适用于中小型Web API项目。依赖：Python 3.8+, FastAPI 0.68+"
                ... )
                "文件上传成功！\\n文档ID: doc_fastapi_template_001\\n已添加到代码模板库"
            """
            try:
                # 从会话上下文获取 user_id
                user_id = self.session_manager.get_current_user_id()
                if not user_id:
                    user_id = self.config.default_user_id
                    logger.warning(f"未找到会话上下文中的user_id，使用默认值: {user_id}")

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
            # 启动会话清理任务
            await self.session_manager.start_cleanup_task()

            # 获取 FastMCP 的 Starlette 应用
            app = self.mcp.sse_app()

            # 添加会话管理中间件
            from starlette.middleware.base import BaseHTTPMiddleware

            class SessionMiddleware(BaseHTTPMiddleware):
                def __init__(self, app, session_manager, config):
                    super().__init__(app)
                    self.session_manager = session_manager
                    self.config = config

                async def dispatch(self, request: Request, call_next):
                    # 解析 URL 参数获取 user_id
                    query_params = dict(request.query_params)
                    user_id = query_params.get("user_id", self.config.default_user_id)

                    # 为此连接创建或获取会话
                    session_id = query_params.get("session_id")
                    if not session_id:
                        session_id = str(uuid.uuid4())

                    # 创建会话
                    await self.session_manager.create_session(user_id, session_id)

                    # 设置会话上下文
                    self.session_manager.set_session_context(session_id, user_id)

                    logger.info(f"处理请求: path={request.url.path}, user_id={user_id}, session_id={session_id}")

                    try:
                        response = await call_next(request)
                        return response
                    finally:
                        # 请求完成后不清除上下文，保持会话活跃
                        pass

            # 包装应用
            app.add_middleware(SessionMiddleware, session_manager=self.session_manager, config=self.config)

            logger.info("SSE MCP 服务器已启动，等待客户端连接...")
            logger.info(f"SSE连接端点: http://{self.config.sse_host}:{self.config.sse_port}{self.config.sse_endpoint}")
            logger.info(f"支持URL参数: user_id (指定用户ID), session_id (可选，自动生成)")

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
        finally:
            # 停止会话清理任务
            await self.session_manager.stop_cleanup_task()

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