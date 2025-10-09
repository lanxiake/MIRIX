"""
MIRIX MCP Server - Memory Get Profile Tool

该模块实现用户记忆档案获取功能，允许获取用户的完整记忆档案概览，
包括个人信息、偏好、历史记录等全面画像信息。

主要功能：
1. 获取用户的完整记忆档案概览
2. 支持按记忆类型过滤档案信息
3. 提供记忆统计和摘要信息
4. 支持档案数据的结构化展示
5. 完整的参数验证和错误处理

作者：MIRIX MCP Server Team
版本：1.0.0
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..mirix_adapter import MIRIXAdapter
from ..exceptions import (
    MCPServerError,
    MIRIXClientError,
    MemoryToolError,
    ValidationError
)
from ..utils import format_timestamp, sanitize_filename

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


class MemoryGetProfileTool:
    """
    记忆档案获取工具类
    
    提供获取用户完整记忆档案概览的功能。
    支持按记忆类型过滤和详细的档案信息展示。
    """
    
    def __init__(self, mirix_adapter: MIRIXAdapter):
        """
        初始化记忆档案获取工具
        
        Args:
            mirix_adapter: MIRIX 后端适配器实例
        """
        self.mirix_adapter = mirix_adapter
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_parameters(
        self,
        memory_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        验证档案获取参数
        
        Args:
            memory_types: 要获取的记忆类型列表（可选）
            
        Returns:
            Dict[str, Any]: 验证后的参数字典
            
        Raises:
            ValidationError: 参数验证失败时抛出
        """
        try:
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
            
            return {
                "memory_types": validated_memory_types
            }
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"参数验证失败: {str(e)}")
    
    def prepare_profile_request(
        self,
        validated_params: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        准备档案获取请求数据
        
        Args:
            validated_params: 验证后的参数
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 档案请求数据
        """
        profile_data = {
            "user_id": user_id
        }
        
        # 添加记忆类型过滤（如果指定）
        if validated_params["memory_types"]:
            profile_data["memory_types"] = validated_params["memory_types"]
        
        return profile_data
    
    def format_profile_response(
        self,
        profile_result: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        格式化档案响应
        
        Args:
            profile_result: MIRIX 后端返回的档案结果
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 格式化后的响应
        """
        profile_data = profile_result.get("profile", {})
        memory_summary = profile_result.get("memory_summary", {})
        total_memories = profile_result.get("total_memories", 0)
        last_updated = profile_result.get("last_updated")
        
        # 格式化个人档案信息
        formatted_profile = {
            "basic_info": profile_data.get("basic_info", {}),
            "preferences": profile_data.get("preferences", {}),
            "skills": profile_data.get("skills", []),
            "interests": profile_data.get("interests", []),
            "personality_traits": profile_data.get("personality_traits", {}),
            "communication_style": profile_data.get("communication_style", {}),
            "goals": profile_data.get("goals", []),
            "context": profile_data.get("context", {})
        }
        
        # 格式化记忆摘要
        formatted_memory_summary = {}
        for memory_type in VALID_MEMORY_TYPES:
            type_summary = memory_summary.get(memory_type, {})
            formatted_memory_summary[memory_type] = {
                "count": type_summary.get("count", 0),
                "recent_updates": type_summary.get("recent_updates", 0),
                "key_topics": type_summary.get("key_topics", []),
                "last_activity": type_summary.get("last_activity")
            }
        
        # 格式化时间信息
        formatted_last_updated = None
        if last_updated:
            try:
                formatted_last_updated = format_timestamp(last_updated)
            except Exception:
                formatted_last_updated = str(last_updated)
        
        return {
            "success": True,
            "user_id": user_id,
            "profile": formatted_profile,
            "memory_summary": formatted_memory_summary,
            "total_memories": total_memories,
            "last_updated": formatted_last_updated,
            "profile_metadata": {
                "profile_completeness": self._calculate_profile_completeness(formatted_profile),
                "memory_distribution": self._calculate_memory_distribution(formatted_memory_summary),
                "activity_level": self._calculate_activity_level(formatted_memory_summary),
                "generated_at": format_timestamp(datetime.now().timestamp())
            }
        }
    
    def _calculate_profile_completeness(self, profile: Dict[str, Any]) -> float:
        """
        计算档案完整度
        
        Args:
            profile: 格式化后的档案数据
            
        Returns:
            float: 完整度百分比（0-100）
        """
        total_fields = 8  # 总字段数
        filled_fields = 0
        
        # 检查各个字段是否有内容
        if profile.get("basic_info"):
            filled_fields += 1
        if profile.get("preferences"):
            filled_fields += 1
        if profile.get("skills"):
            filled_fields += 1
        if profile.get("interests"):
            filled_fields += 1
        if profile.get("personality_traits"):
            filled_fields += 1
        if profile.get("communication_style"):
            filled_fields += 1
        if profile.get("goals"):
            filled_fields += 1
        if profile.get("context"):
            filled_fields += 1
        
        return round((filled_fields / total_fields) * 100, 2)
    
    def _calculate_memory_distribution(self, memory_summary: Dict[str, Any]) -> Dict[str, float]:
        """
        计算记忆分布
        
        Args:
            memory_summary: 记忆摘要数据
            
        Returns:
            Dict[str, float]: 各类型记忆的百分比分布
        """
        total_count = sum(
            summary.get("count", 0) 
            for summary in memory_summary.values()
        )
        
        if total_count == 0:
            return {memory_type: 0.0 for memory_type in VALID_MEMORY_TYPES}
        
        distribution = {}
        for memory_type in VALID_MEMORY_TYPES:
            count = memory_summary.get(memory_type, {}).get("count", 0)
            distribution[memory_type] = round((count / total_count) * 100, 2)
        
        return distribution
    
    def _calculate_activity_level(self, memory_summary: Dict[str, Any]) -> str:
        """
        计算活动水平
        
        Args:
            memory_summary: 记忆摘要数据
            
        Returns:
            str: 活动水平描述（high, medium, low, inactive）
        """
        total_recent_updates = sum(
            summary.get("recent_updates", 0) 
            for summary in memory_summary.values()
        )
        
        if total_recent_updates >= 20:
            return "high"
        elif total_recent_updates >= 10:
            return "medium"
        elif total_recent_updates >= 1:
            return "low"
        else:
            return "inactive"
    
    async def get_user_profile(
        self,
        memory_types: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户记忆档案
        
        Args:
            memory_types: 要获取的记忆类型列表（可选）
            user_id: 用户ID（可选，使用默认用户ID如果未提供）
            
        Returns:
            Dict[str, Any]: 用户档案结果
            
        Raises:
            MemoryToolError: 档案获取操作失败时抛出
        """
        try:
            # 验证参数
            validated_params = self.validate_parameters(memory_types)
            
            # 获取用户ID
            if not user_id:
                user_id = "default_user"
            
            # 准备档案请求
            profile_data = self.prepare_profile_request(validated_params, user_id)
            
            self.logger.info(
                f"开始获取用户档案: user_id={user_id}, "
                f"memory_types={validated_params['memory_types']}"
            )
            
            # 调用 MIRIX 后端获取用户档案
            profile_result = await self.mirix_adapter.get_user_profile(profile_data)
            
            # 格式化响应
            response = self.format_profile_response(profile_result, user_id)
            
            self.logger.info(
                f"用户档案获取完成: total_memories={response['total_memories']}, "
                f"completeness={response['profile_metadata']['profile_completeness']}%"
            )
            
            return response
            
        except ValidationError as e:
            self.logger.error(f"档案获取参数验证失败: {e}")
            raise MemoryToolError(f"档案获取参数无效: {str(e)}")
        
        except MIRIXClientError as e:
            self.logger.error(f"MIRIX 客户端档案获取失败: {e}")
            raise MemoryToolError(f"用户档案获取失败: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"用户档案获取意外错误: {e}")
            raise MemoryToolError(f"用户档案获取失败: {str(e)}")


# 便捷函数接口
async def memory_get_profile(
    memory_types: Optional[List[str]] = None,
    user_id: Optional[str] = None,
    mirix_adapter: Optional[MIRIXAdapter] = None
) -> Dict[str, Any]:
    """
    获取用户的完整记忆档案概览
    
    这是一个便捷函数，提供简单的接口来获取用户的完整记忆档案。
    包括个人信息、偏好、历史记录等全面画像信息。
    
    使用场景：
    - 初次与用户交互时，了解用户背景
    - 需要全面了解用户偏好和特点时
    - 为用户提供个性化建议前的信息收集
    - 定期回顾和更新对用户的了解
    
    执行顺序：
    - 通常在对话开始时使用，为后续交互提供基础
    - 可以在其他记忆工具之前使用，了解用户全貌
    - 适合在需要个性化服务时调用
    
    Args:
        memory_types (Optional[List[str]]): 要获取的记忆类型列表
            - 可选参数，用于过滤特定类型的记忆档案
            - 支持的类型：
              * "core": 核心记忆（基本个人信息、重要偏好）
              * "episodic": 情节记忆（具体事件、经历）
              * "semantic": 语义记忆（知识、概念、事实）
              * "procedural": 程序记忆（技能、习惯、流程）
              * "resource": 资源记忆（文件、链接、工具）
              * "knowledge_vault": 知识库（结构化知识存储）
            - 如果未提供，将获取所有类型的记忆档案
            - 示例：["core", "semantic"] 或 ["episodic", "procedural"]
        
        user_id (Optional[str]): 用户ID
            - 可选参数，如果未提供将使用默认用户ID
            - 用于指定要获取哪个用户的档案
        
        mirix_adapter (Optional[MIRIXAdapter]): MIRIX 适配器实例
            - 可选参数，如果未提供将创建新实例
            - 用于与 MIRIX 后端通信
    
    Returns:
        Dict[str, Any]: 用户档案结果字典，包含以下字段：
            - success (bool): 操作是否成功
            - user_id (str): 用户ID
            - profile (Dict): 用户档案信息，包含：
              * basic_info: 基本信息
              * preferences: 偏好设置
              * skills: 技能列表
              * interests: 兴趣爱好
              * personality_traits: 性格特征
              * communication_style: 沟通风格
              * goals: 目标列表
              * context: 上下文信息
            - memory_summary (Dict): 记忆摘要，按类型分组，每个类型包含：
              * count: 记忆数量
              * recent_updates: 最近更新数量
              * key_topics: 关键主题
              * last_activity: 最后活动时间
            - total_memories (int): 总记忆数量
            - last_updated (str): 最后更新时间
            - profile_metadata (Dict): 档案元数据，包含：
              * profile_completeness: 档案完整度百分比
              * memory_distribution: 记忆类型分布
              * activity_level: 活动水平
              * generated_at: 生成时间
    
    Raises:
        MemoryToolError: 档案获取操作失败时抛出
        ValidationError: 参数验证失败时抛出
        MIRIXClientError: MIRIX 客户端通信失败时抛出
    
    Examples:
        # 获取完整用户档案
        result = await memory_get_profile()
        
        # 获取特定类型的记忆档案
        result = await memory_get_profile(
            memory_types=["core", "preferences"]
        )
        
        # 获取指定用户的档案
        result = await memory_get_profile(
            user_id="user123"
        )
        
        # 检查档案结果
        if result["success"]:
            profile = result["profile"]
            print(f"用户档案完整度: {result['profile_metadata']['profile_completeness']}%")
            print(f"总记忆数量: {result['total_memories']}")
            print(f"基本信息: {profile['basic_info']}")
            print(f"偏好设置: {profile['preferences']}")
        else:
            print(f"档案获取失败: {result.get('error', '未知错误')}")
    """
    # 创建或使用提供的适配器
    if mirix_adapter is None:
        from ..config import get_config
        mirix_adapter = MIRIXAdapter(get_config())
    
    # 创建档案获取工具实例
    profile_tool = MemoryGetProfileTool(mirix_adapter)
    
    # 执行档案获取
    return await profile_tool.get_user_profile(memory_types, user_id)


# 工具元数据，用于 MCP 工具注册
TOOL_METADATA = {
    "name": "memory_get_profile",
    "description": "获取用户的完整记忆档案概览",
    "inputSchema": {
        "type": "object",
        "properties": {
            "memory_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": "要获取的记忆类型列表（可选）"
            }
        }
    },
    "returns": {
        "type": "object",
        "description": "用户档案信息，包含个人信息、偏好、记忆摘要等"
    },
    "examples": [
        {
            "description": "获取完整用户档案",
            "parameters": {}
        },
        {
            "description": "获取特定类型的记忆档案",
            "parameters": {
                "memory_types": ["core", "semantic"]
            }
        }
    ]
}