"""
MIRIX MCP Server - Memory Search Tool

该模块实现记忆搜索功能，允许在用户的记忆系统中搜索相关信息。
支持多种记忆类型的搜索，并提供灵活的查询参数配置。

主要功能：
1. 在用户记忆系统中搜索相关信息
2. 支持多种记忆类型过滤
3. 可配置搜索结果数量限制
4. 提供详细的搜索结果和统计信息
5. 完整的参数验证和错误处理

作者：MIRIX MCP Server Team
版本：1.0.0
"""

import logging
from typing import Any, Dict, List, Optional

from ..mirix_adapter import MIRIXAdapter
from ..exceptions import (
    MCPServerError,
    MIRIXClientError,
    MemoryToolError,
    ValidationError
)
from ..utils import truncate_string, sanitize_filename

# 配置日志记录器
logger = logging.getLogger(__name__)

# 支持的记忆类型常量
VALID_MEMORY_TYPES = [
    "core",           # 核心记忆：基本个人信息、重要偏好
    "episodic",       # 情节记忆：具体事件、经历
    "semantic",       # 语义记忆：知识、概念、事实
    "procedural",     # 程序记忆：技能、习惯、流程
    "resource",       # 资源记忆：文件、链接、工具
    "knowledge_vault" # 知识库：结构化知识存储
]

# 搜索配置常量
MAX_SEARCH_LIMIT = 50      # 最大搜索结果数量
DEFAULT_SEARCH_LIMIT = 10  # 默认搜索结果数量
MIN_QUERY_LENGTH = 1       # 最小查询长度
MAX_QUERY_LENGTH = 1000    # 最大查询长度


class MemorySearchTool:
    """
    记忆搜索工具类
    
    提供在 MIRIX 记忆系统中搜索相关信息的功能。
    支持多种记忆类型过滤和灵活的查询参数配置。
    """
    
    def __init__(self, mirix_adapter: MIRIXAdapter):
        """
        初始化记忆搜索工具
        
        Args:
            mirix_adapter: MIRIX 后端适配器实例
        """
        self.mirix_adapter = mirix_adapter
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_parameters(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = DEFAULT_SEARCH_LIMIT
    ) -> Dict[str, Any]:
        """
        验证搜索参数
        
        Args:
            query: 搜索查询字符串
            memory_types: 要搜索的记忆类型列表（可选）
            limit: 搜索结果数量限制
            
        Returns:
            Dict[str, Any]: 验证后的参数字典
            
        Raises:
            ValidationError: 参数验证失败时抛出
        """
        try:
            # 验证查询字符串
            if not query or not query.strip():
                raise ValidationError("搜索查询不能为空")
            
            # 验证查询长度
            if len(query) < MIN_QUERY_LENGTH or len(query) > MAX_QUERY_LENGTH:
                raise ValidationError(
                    f"查询长度必须在 {MIN_QUERY_LENGTH}-{MAX_QUERY_LENGTH} 字符之间"
                )
            
            # 清理查询字符串
            cleaned_query = query.strip()
            
            # 验证记忆类型
            validated_memory_types = None
            if memory_types:
                if not isinstance(memory_types, list):
                    raise ValidationError("memory_types 必须是列表类型")
                
                # 检查无效的记忆类型
                invalid_types = [t for t in memory_types if t not in VALID_MEMORY_TYPES]
                if invalid_types:
                    raise ValidationError(
                        f"无效的记忆类型: {', '.join(invalid_types)}。"
                        f"支持的类型: {', '.join(VALID_MEMORY_TYPES)}"
                    )
                
                validated_memory_types = list(set(memory_types))  # 去重
            
            # 验证搜索限制
            if not isinstance(limit, int) or limit < 1:
                raise ValidationError("搜索限制必须是正整数")
            
            if limit > MAX_SEARCH_LIMIT:
                self.logger.warning(
                    f"搜索限制 {limit} 超过最大值 {MAX_SEARCH_LIMIT}，将使用最大值"
                )
                limit = MAX_SEARCH_LIMIT
            
            return {
                "query": cleaned_query,
                "memory_types": validated_memory_types,
                "limit": limit
            }
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"参数验证失败: {str(e)}")
    
    def prepare_search_request(
        self,
        validated_params: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        准备搜索请求数据
        
        Args:
            validated_params: 验证后的参数
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 搜索请求数据
        """
        search_data = {
            "query": validated_params["query"],
            "user_id": user_id,
            "limit": validated_params["limit"]
        }
        
        # 添加记忆类型过滤（如果指定）
        if validated_params["memory_types"]:
            search_data["memory_types"] = validated_params["memory_types"]
        
        return search_data
    
    def format_search_response(
        self,
        search_result: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """
        格式化搜索响应
        
        Args:
            search_result: MIRIX 后端返回的搜索结果
            query: 原始查询字符串
            
        Returns:
            Dict[str, Any]: 格式化后的响应
        """
        memories = search_result.get("memories", [])
        total_count = search_result.get("total_count", len(memories))
        
        # 格式化记忆条目
        formatted_memories = []
        for memory in memories:
            formatted_memory = {
                "id": memory.get("id"),
                "content": memory.get("content", ""),
                "memory_type": memory.get("memory_type", "unknown"),
                "context": memory.get("context"),
                "relevance_score": memory.get("relevance_score", 0.0),
                "created_at": memory.get("created_at"),
                "updated_at": memory.get("updated_at")
            }
            formatted_memories.append(formatted_memory)
        
        return {
            "success": True,
            "query": query,
            "memories": formatted_memories,
            "total_count": total_count,
            "returned_count": len(formatted_memories),
            "search_metadata": {
                "query_length": len(query),
                "has_more_results": total_count > len(formatted_memories)
            }
        }
    
    async def search_memory(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = DEFAULT_SEARCH_LIMIT,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行记忆搜索
        
        Args:
            query: 搜索查询字符串
            memory_types: 要搜索的记忆类型列表（可选）
            limit: 搜索结果数量限制
            user_id: 用户ID（可选，使用默认用户ID如果未提供）
            
        Returns:
            Dict[str, Any]: 搜索结果
            
        Raises:
            MemoryToolError: 搜索操作失败时抛出
        """
        try:
            # 验证参数
            validated_params = self.validate_parameters(query, memory_types, limit)
            
            # 获取用户ID
            if not user_id:
                user_id = "default_user"
            
            # 准备搜索请求
            search_data = self.prepare_search_request(validated_params, user_id)
            
            self.logger.info(
                f"开始搜索记忆: query='{validated_params['query'][:50]}...', "
                f"types={validated_params['memory_types']}, limit={validated_params['limit']}"
            )
            
            # 调用 MIRIX 后端搜索记忆
            search_result = await self.mirix_adapter.search_memory(search_data)
            
            # 格式化响应
            response = self.format_search_response(search_result, validated_params["query"])
            
            self.logger.info(
                f"记忆搜索完成: 找到 {response['returned_count']} 条记忆 "
                f"(总计 {response['total_count']} 条)"
            )
            
            return response
            
        except ValidationError as e:
            self.logger.error(f"搜索参数验证失败: {e}")
            raise MemoryToolError(f"搜索参数无效: {str(e)}")
        
        except MIRIXClientError as e:
            self.logger.error(f"MIRIX 客户端搜索失败: {e}")
            raise MemoryToolError(f"记忆搜索失败: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"记忆搜索意外错误: {e}")
            raise MemoryToolError(f"记忆搜索失败: {str(e)}")


# 便捷函数接口
async def memory_search(
    query: str,
    memory_types: Optional[List[str]] = None,
    limit: int = DEFAULT_SEARCH_LIMIT,
    user_id: Optional[str] = None,
    mirix_adapter: Optional[MIRIXAdapter] = None
) -> Dict[str, Any]:
    """
    在用户记忆系统中搜索相关信息
    
    这是一个便捷函数，提供简单的接口来搜索用户记忆。
    支持多种记忆类型过滤和灵活的查询参数配置。
    
    使用场景：
    - 用户询问之前讨论过的话题时使用
    - 需要回忆用户的偏好、习惯或个人信息时
    - 查找相关的知识、经验或程序步骤
    - 在回答问题前，先检索相关的背景信息
    
    执行顺序：
    - 通常在 memory_add 之前使用，避免重复存储
    - 在回答用户问题前使用，获取相关背景信息
    - 可以与 memory_chat 结合使用，提供更好的上下文
    
    Args:
        query (str): 搜索查询字符串
            - 必填参数，描述要搜索的内容
            - 长度限制：1-1000 字符
            - 示例："用户喜欢的编程语言"、"上次讨论的项目"
        
        memory_types (Optional[List[str]]): 要搜索的记忆类型列表
            - 可选参数，用于过滤特定类型的记忆
            - 支持的类型：
              * "core": 核心记忆（基本个人信息、重要偏好）
              * "episodic": 情节记忆（具体事件、经历）
              * "semantic": 语义记忆（知识、概念、事实）
              * "procedural": 程序记忆（技能、习惯、流程）
              * "resource": 资源记忆（文件、链接、工具）
              * "knowledge_vault": 知识库（结构化知识存储）
            - 示例：["core", "semantic"] 或 ["episodic"]
        
        limit (int): 搜索结果数量限制
            - 可选参数，默认值：10
            - 取值范围：1-50
            - 用于控制返回的记忆条目数量
        
        user_id (Optional[str]): 用户ID
            - 可选参数，如果未提供将使用默认用户ID
            - 用于指定要搜索哪个用户的记忆
        
        mirix_adapter (Optional[MIRIXAdapter]): MIRIX 适配器实例
            - 可选参数，如果未提供将创建新实例
            - 用于与 MIRIX 后端通信
    
    Returns:
        Dict[str, Any]: 搜索结果字典，包含以下字段：
            - success (bool): 操作是否成功
            - query (str): 原始搜索查询
            - memories (List[Dict]): 搜索到的记忆列表，每个记忆包含：
              * id: 记忆唯一标识符
              * content: 记忆内容
              * memory_type: 记忆类型
              * context: 记忆上下文（可选）
              * relevance_score: 相关性评分
              * created_at: 创建时间
              * updated_at: 更新时间
            - total_count (int): 总记忆数量
            - returned_count (int): 返回的记忆数量
            - search_metadata (Dict): 搜索元数据
    
    Raises:
        MemoryToolError: 搜索操作失败时抛出
        ValidationError: 参数验证失败时抛出
        MIRIXClientError: MIRIX 客户端通信失败时抛出
    
    Examples:
        # 基本搜索
        result = await memory_search("用户的编程偏好")
        
        # 搜索特定类型的记忆
        result = await memory_search(
            "Python 相关知识",
            memory_types=["semantic", "procedural"]
        )
        
        # 限制搜索结果数量
        result = await memory_search(
            "最近的对话",
            memory_types=["episodic"],
            limit=5
        )
        
        # 检查搜索结果
        if result["success"]:
            print(f"找到 {result['returned_count']} 条相关记忆")
            for memory in result["memories"]:
                print(f"- {memory['memory_type']}: {memory['content'][:100]}...")
        else:
            print(f"搜索失败: {result.get('error', '未知错误')}")
    """
    # 创建或使用提供的适配器
    if mirix_adapter is None:
        from ..config import get_config
        mirix_adapter = MIRIXAdapter(get_config())
    
    # 创建搜索工具实例
    search_tool = MemorySearchTool(mirix_adapter)
    
    # 执行搜索
    return await search_tool.search_memory(query, memory_types, limit, user_id)


# 工具元数据，用于 MCP 工具注册
TOOL_METADATA = {
    "name": "memory_search",
    "description": "在用户记忆系统中搜索相关信息",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索查询字符串"
            },
            "memory_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": "要搜索的记忆类型列表（可选）"
            },
            "limit": {
                "type": "integer",
                "description": "搜索结果数量限制（默认：10，最大：50）",
                "default": DEFAULT_SEARCH_LIMIT
            }
        },
        "required": ["query"]
    },
    "returns": {
        "type": "object",
        "description": "搜索结果，包含记忆列表和统计信息"
    },
    "examples": [
        {
            "description": "搜索用户的编程偏好",
            "parameters": {
                "query": "用户喜欢的编程语言和框架"
            }
        },
        {
            "description": "搜索特定类型的记忆",
            "parameters": {
                "query": "Python 相关知识",
                "memory_types": ["semantic", "procedural"],
                "limit": 5
            }
        }
    ]
}