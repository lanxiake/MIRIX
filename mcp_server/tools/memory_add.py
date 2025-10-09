"""
Memory Add Tool - 记忆添加工具

该模块实现了向 MIRIX 记忆系统添加新信息的功能。
这是记忆管理的核心工具之一，用于将重要信息存储到用户的个人记忆库中。

功能特点：
1. 支持多种记忆类型（core, episodic, semantic, procedural, resource, knowledge_vault）
2. 提供完整的参数验证和错误处理
3. 支持上下文信息的添加
4. 自动记录操作日志
5. 返回标准化的响应格式

使用场景：
- 当用户分享个人信息、偏好或重要事实时使用
- 学习新知识或技能时，将关键信息存储起来
- 记录重要的对话内容或决定
- 保存工作流程、步骤说明等程序性知识

执行顺序：通常是对话中的第一步，在获取到有价值信息后立即使用
预期效果：信息被永久存储，可通过 memory_search 检索，增强 AI 对用户的了解
"""

from typing import Any, Dict, Optional
import logging

from ..mirix_adapter import MIRIXAdapter
from ..exceptions import ValidationError, MemoryToolError, handle_exception
from ..utils import validate_required_fields, validate_field_type, get_logger

# 获取模块日志器
logger = get_logger(__name__)

# 支持的记忆类型常量
VALID_MEMORY_TYPES = [
    "core",           # 个人信息：基本信息、偏好、特征等
    "episodic",       # 事件记忆：具体发生的事件、经历
    "semantic",       # 知识记忆：概念、事实、规则等
    "procedural",     # 程序记忆：步骤、流程、技能等
    "resource",       # 资源记忆：文档、链接、文件等
    "knowledge_vault" # 知识库：参考数据、百科信息等
]


class MemoryAddTool:
    """
    记忆添加工具类
    
    负责处理向 MIRIX 记忆系统添加新信息的所有逻辑，
    包括参数验证、数据处理、错误处理等。
    
    Attributes:
        mirix_adapter: MIRIX 客户端适配器实例
        tool_name: 工具名称，用于日志和错误处理
    """
    
    def __init__(self, mirix_adapter: MIRIXAdapter):
        """
        初始化记忆添加工具
        
        Args:
            mirix_adapter: MIRIX 客户端适配器实例
        """
        self.mirix_adapter = mirix_adapter
        self.tool_name = "memory_add"
        logger.info(f"初始化 {self.tool_name} 工具")
    
    def validate_parameters(self, content: str, memory_type: str, context: Optional[str] = None) -> None:
        """
        验证工具参数
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            context: 上下文信息（可选）
            
        Raises:
            ValidationError: 当参数验证失败时
        """
        # 验证必需参数
        if not content or not content.strip():
            raise ValidationError(
                "记忆内容不能为空",
                field_name="content",
                field_value=content
            )
        
        if not memory_type or not memory_type.strip():
            raise ValidationError(
                "记忆类型不能为空",
                field_name="memory_type",
                field_value=memory_type
            )
        
        # 验证参数类型
        validate_field_type(content, str, "content")
        validate_field_type(memory_type, str, "memory_type")
        if context is not None:
            validate_field_type(context, str, "context")
        
        # 验证记忆类型是否有效
        if memory_type not in VALID_MEMORY_TYPES:
            raise ValidationError(
                f"无效的记忆类型 '{memory_type}'，支持的类型: {', '.join(VALID_MEMORY_TYPES)}",
                field_name="memory_type",
                field_value=memory_type,
                details={
                    "valid_types": VALID_MEMORY_TYPES,
                    "provided_type": memory_type
                }
            )
        
        # 验证内容长度（避免过长的内容）
        max_content_length = 10000  # 10KB 限制
        if len(content) > max_content_length:
            raise ValidationError(
                f"记忆内容过长，最大支持 {max_content_length} 字符，当前 {len(content)} 字符",
                field_name="content",
                field_value=f"内容长度: {len(content)}",
                details={
                    "max_length": max_content_length,
                    "actual_length": len(content)
                }
            )
        
        # 验证上下文长度（如果提供）
        if context and len(context) > 1000:  # 1KB 限制
            raise ValidationError(
                f"上下文信息过长，最大支持 1000 字符，当前 {len(context)} 字符",
                field_name="context",
                field_value=f"上下文长度: {len(context)}",
                details={
                    "max_length": 1000,
                    "actual_length": len(context)
                }
            )
    
    def prepare_request_data(
        self, 
        content: str, 
        memory_type: str, 
        context: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        准备发送给 MIRIX 后端的请求数据
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            context: 上下文信息
            user_id: 用户ID（如果未提供，使用配置中的默认值）
            
        Returns:
            格式化的请求数据字典
        """
        request_data = {
            "content": content.strip(),
            "memory_type": memory_type.strip().lower(),
            "user_id": user_id or self.mirix_adapter.config.default_user_id
        }
        
        # 添加可选的上下文信息
        if context and context.strip():
            request_data["context"] = context.strip()
        
        # 添加时间戳和元数据
        from ..utils import get_current_iso_time, generate_unique_id
        request_data.update({
            "timestamp": get_current_iso_time(),
            "source": "mcp_server",
            "tool_name": self.tool_name,
            "request_id": generate_unique_id()
        })
        
        return request_data
    
    def format_success_response(
        self, 
        result: Dict[str, Any], 
        memory_type: str,
        content: str
    ) -> Dict[str, Any]:
        """
        格式化成功响应
        
        Args:
            result: MIRIX 后端返回的结果
            memory_type: 记忆类型
            content: 记忆内容
            
        Returns:
            标准化的成功响应
        """
        return {
            "success": True,
            "message": "记忆添加成功",
            "data": {
                "memory_id": result.get("memory_id"),
                "memory_type": memory_type,
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
                "timestamp": result.get("timestamp"),
                "status": "stored"
            },
            "metadata": {
                "tool_name": self.tool_name,
                "operation": "add_memory",
                "backend_response": result
            }
        }
    
    async def execute(
        self, 
        content: str, 
        memory_type: str, 
        context: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行记忆添加操作
        
        这是工具的主要执行方法，负责协调整个添加流程。
        
        Args:
            content: 要存储的记忆内容
            memory_type: 记忆类型
            context: 可选的上下文信息
            user_id: 用户ID（可选，默认使用配置中的值）
            
        Returns:
            包含操作结果的字典
            
        Raises:
            ValidationError: 参数验证失败
            MemoryToolError: 记忆操作失败
        """
        try:
            logger.info(f"开始执行 {self.tool_name}，记忆类型: {memory_type}")
            
            # 1. 验证参数
            self.validate_parameters(content, memory_type, context)
            logger.debug("参数验证通过")
            
            # 2. 准备请求数据
            request_data = self.prepare_request_data(content, memory_type, context, user_id)
            logger.debug(f"请求数据准备完成: {request_data.get('request_id')}")
            
            # 3. 调用 MIRIX 后端
            result = await self.mirix_adapter.add_memory(request_data)
            logger.info(f"MIRIX 后端调用成功，记忆ID: {result.get('memory_id')}")
            
            # 4. 格式化响应
            response = self.format_success_response(result, memory_type, content)
            logger.info(f"{self.tool_name} 执行成功")
            
            return response
            
        except ValidationError:
            # 参数验证错误，直接重新抛出
            logger.warning(f"{self.tool_name} 参数验证失败")
            raise
            
        except Exception as e:
            # 其他错误，包装为 MemoryToolError
            error_msg = f"记忆添加失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            handle_exception(
                e, 
                context=f"{self.tool_name} 执行过程中",
                reraise_as=MemoryToolError
            )


# 工具函数接口

async def memory_add(
    content: str,
    memory_type: str,
    context: Optional[str] = None,
    mirix_adapter: Optional[MIRIXAdapter] = None
) -> Dict[str, Any]:
    """
    记忆添加工具函数接口
    
    这是一个便捷的函数接口，用于直接调用记忆添加功能。
    
    Args:
        content: 要存储的记忆内容，应该是完整、有意义的信息片段
        memory_type: 记忆类型，必须是以下之一：
                    - core: 个人信息（偏好、特征等）
                    - episodic: 事件记忆（具体经历）
                    - semantic: 知识记忆（概念、事实）
                    - procedural: 程序记忆（步骤、流程）
                    - resource: 资源记忆（文档、链接）
                    - knowledge_vault: 知识库（参考数据）
        context: 可选的上下文信息，帮助理解内容的背景
        mirix_adapter: MIRIX 适配器实例，如果未提供则使用默认实例
        
    Returns:
        包含操作结果的字典，格式如下：
        {
            "success": bool,
            "message": str,
            "data": {
                "memory_id": str,
                "memory_type": str,
                "content_preview": str,
                "timestamp": str,
                "status": str
            },
            "metadata": dict
        }
        
    Raises:
        ValidationError: 当参数验证失败时
        MemoryToolError: 当记忆操作失败时
        
    Example:
        >>> result = await memory_add(
        ...     content="用户喜欢喝咖啡，特别是拿铁",
        ...     memory_type="core",
        ...     context="用户偏好信息"
        ... )
        >>> print(result["success"])  # True
        >>> print(result["data"]["memory_id"])  # "mem_12345..."
    """
    # 如果没有提供适配器，创建默认实例
    if mirix_adapter is None:
        from ..config import get_config
        from ..mirix_adapter import MIRIXAdapter
        
        config = get_config()
        mirix_adapter = MIRIXAdapter(config)
    
    # 创建工具实例并执行
    tool = MemoryAddTool(mirix_adapter)
    return await tool.execute(content, memory_type, context)


# 工具元数据
TOOL_METADATA = {
    "name": "memory_add",
    "description": "向 MIRIX 记忆系统添加新信息",
    "category": "memory",
    "version": "1.0.0",
    "inputSchema": {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "要存储的记忆内容，应该是完整、有意义的信息片段",
                "maxLength": 10000
            },
            "memory_type": {
                "type": "string",
                "enum": VALID_MEMORY_TYPES,
                "description": "记忆类型，决定信息的分类和存储方式"
            },
            "context": {
                "type": "string",
                "description": "可选的上下文信息，帮助理解内容的背景",
                "maxLength": 1000
            }
        },
        "required": ["content", "memory_type"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "data": {"type": "object"},
            "metadata": {"type": "object"}
        }
    },
    "examples": [
        {
            "description": "添加个人偏好信息",
            "input": {
                "content": "用户喜欢喝咖啡，特别是拿铁",
                "memory_type": "core",
                "context": "用户偏好"
            },
            "output": {
                "success": True,
                "message": "记忆添加成功",
                "data": {
                    "memory_id": "mem_12345",
                    "memory_type": "core",
                    "status": "stored"
                }
            }
        },
        {
            "description": "添加学习记录",
            "input": {
                "content": "学习了 Python 的装饰器概念，理解了其工作原理",
                "memory_type": "semantic",
                "context": "编程学习"
            },
            "output": {
                "success": True,
                "message": "记忆添加成功",
                "data": {
                    "memory_id": "mem_67890",
                    "memory_type": "semantic",
                    "status": "stored"
                }
            }
        }
    ],
    "usage_scenarios": [
        "用户分享个人信息、偏好或重要事实",
        "学习新知识或技能时存储关键信息",
        "记录重要的对话内容或决定",
        "保存工作流程、步骤说明等程序性知识"
    ],
    "execution_order": "通常是对话中的第一步，在获取到有价值信息后立即使用",
    "expected_effect": "信息被永久存储，可通过 memory_search 检索，增强 AI 对用户的了解"
}