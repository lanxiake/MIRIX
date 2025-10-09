"""
MIRIX MCP Server - Memory Chat Tool

该模块实现基于记忆的对话功能，允许用户与 AI 进行个性化对话，
同时自动管理记忆存储和检索，提供连贯的对话体验。

主要功能：
1. 基于用户记忆的个性化对话
2. 自动记忆存储和管理
3. 支持多模态输入（文本和图像）
4. 智能记忆化控制
5. 完整的对话上下文管理

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

# 对话配置常量
MIN_MESSAGE_LENGTH = 1        # 最小消息长度
MAX_MESSAGE_LENGTH = 10000    # 最大消息长度
MAX_IMAGE_URIS = 10          # 最大图像URI数量
DEFAULT_MEMORIZING = True     # 默认记忆化设置


class MemoryChatTool:
    """
    记忆对话工具类
    
    提供基于 MIRIX 记忆系统的个性化对话功能。
    支持自动记忆管理和多模态输入。
    """
    
    def __init__(self, mirix_adapter: MIRIXAdapter):
        """
        初始化记忆对话工具
        
        Args:
            mirix_adapter: MIRIX 后端适配器实例
        """
        self.mirix_adapter = mirix_adapter
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_parameters(
        self,
        message: str,
        memorizing: bool = DEFAULT_MEMORIZING,
        image_uris: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        验证对话参数
        
        Args:
            message: 对话消息内容
            memorizing: 是否启用记忆化
            image_uris: 图像URI列表（可选）
            
        Returns:
            Dict[str, Any]: 验证后的参数字典
            
        Raises:
            ValidationError: 参数验证失败时抛出
        """
        try:
            # 验证消息内容
            if not message or not message.strip():
                raise ValidationError("对话消息不能为空")
            
            # 验证消息长度
            if len(message) < MIN_MESSAGE_LENGTH or len(message) > MAX_MESSAGE_LENGTH:
                raise ValidationError(
                    f"消息长度必须在 {MIN_MESSAGE_LENGTH}-{MAX_MESSAGE_LENGTH} 字符之间"
                )
            
            # 清理消息内容
            cleaned_message = message.strip()
            
            # 验证记忆化参数
            if not isinstance(memorizing, bool):
                raise ValidationError("memorizing 参数必须是布尔值")
            
            # 验证图像URI
            validated_image_uris = None
            if image_uris:
                if not isinstance(image_uris, list):
                    raise ValidationError("image_uris 必须是列表类型")
                
                if len(image_uris) > MAX_IMAGE_URIS:
                    raise ValidationError(f"图像URI数量不能超过 {MAX_IMAGE_URIS} 个")
                
                # 验证每个URI的格式
                validated_uris = []
                for i, uri in enumerate(image_uris):
                    if not isinstance(uri, str) or not uri.strip():
                        raise ValidationError(f"图像URI[{i}] 不能为空")
                    
                    cleaned_uri = uri.strip()
                    if not (cleaned_uri.startswith('http://') or cleaned_uri.startswith('https://')):
                        raise ValidationError(f"图像URI[{i}] 格式无效: {cleaned_uri}")
                    
                    validated_uris.append(cleaned_uri)
                
                validated_image_uris = validated_uris
            
            return {
                "message": cleaned_message,
                "memorizing": memorizing,
                "image_uris": validated_image_uris
            }
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"参数验证失败: {str(e)}")
    
    def prepare_chat_request(
        self,
        validated_params: Dict[str, Any],
        user_id: str,
        ai_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        准备对话请求数据
        
        Args:
            validated_params: 验证后的参数
            user_id: 用户ID
            ai_model: AI模型名称（可选）
            
        Returns:
            Dict[str, Any]: 对话请求数据
        """
        chat_data = {
            "message": validated_params["message"],
            "user_id": user_id,
            "memorizing": validated_params["memorizing"]
        }
        
        # 添加AI模型配置（如果指定）
        if ai_model:
            chat_data["model"] = ai_model
        
        # 添加图像URI（如果提供）
        if validated_params["image_uris"]:
            chat_data["image_uris"] = validated_params["image_uris"]
        
        return chat_data
    
    def format_chat_response(
        self,
        chat_result: Dict[str, Any],
        original_message: str
    ) -> Dict[str, Any]:
        """
        格式化对话响应
        
        Args:
            chat_result: MIRIX 后端返回的对话结果
            original_message: 原始消息内容
            
        Returns:
            Dict[str, Any]: 格式化后的响应
        """
        response_text = chat_result.get("response", "")
        memorized = chat_result.get("memorized", False)
        memory_updates = chat_result.get("memory_updates", [])
        
        # 格式化记忆更新信息
        formatted_memory_updates = []
        for update in memory_updates:
            formatted_update = {
                "action": update.get("action", "unknown"),  # add, update, delete
                "memory_type": update.get("memory_type", "unknown"),
                "content_preview": update.get("content", "")[:100] + "..." if len(update.get("content", "")) > 100 else update.get("content", ""),
                "memory_id": update.get("memory_id")
            }
            formatted_memory_updates.append(formatted_update)
        
        return {
            "success": True,
            "response": response_text,
            "memorized": memorized,
            "memory_updates": formatted_memory_updates,
            "chat_metadata": {
                "message_length": len(original_message),
                "response_length": len(response_text),
                "memory_updates_count": len(formatted_memory_updates),
                "has_multimodal_input": bool(chat_result.get("image_uris"))
            }
        }
    
    async def send_chat_message(
        self,
        message: str,
        memorizing: bool = DEFAULT_MEMORIZING,
        image_uris: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        ai_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送对话消息并获取响应
        
        Args:
            message: 对话消息内容
            memorizing: 是否启用记忆化
            image_uris: 图像URI列表（可选）
            user_id: 用户ID（可选，使用默认用户ID如果未提供）
            ai_model: AI模型名称（可选）
            
        Returns:
            Dict[str, Any]: 对话结果
            
        Raises:
            MemoryToolError: 对话操作失败时抛出
        """
        try:
            # 验证参数
            validated_params = self.validate_parameters(message, memorizing, image_uris)
            
            # 获取用户ID
            if not user_id:
                user_id = "default_user"  # 使用默认用户ID
            
            # 准备对话请求
            chat_data = self.prepare_chat_request(validated_params, user_id, ai_model)
            
            self.logger.info(
                f"开始记忆对话: message_length={len(validated_params['message'])}, "
                f"memorizing={validated_params['memorizing']}, "
                f"has_images={bool(validated_params['image_uris'])}"
            )
            
            # 调用 MIRIX 后端进行对话
            chat_result = await self.mirix_adapter.chat_with_memory(chat_data)
            
            # 格式化响应
            response = self.format_chat_response(chat_result, validated_params["message"])
            
            self.logger.info(
                f"记忆对话完成: response_length={response['chat_metadata']['response_length']}, "
                f"memorized={response['memorized']}, "
                f"memory_updates={response['chat_metadata']['memory_updates_count']}"
            )
            
            return response
            
        except ValidationError as e:
            self.logger.error(f"对话参数验证失败: {e}")
            raise MemoryToolError(f"对话参数无效: {str(e)}")
        
        except MIRIXClientError as e:
            self.logger.error(f"MIRIX 客户端对话失败: {e}")
            raise MemoryToolError(f"记忆对话失败: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"记忆对话意外错误: {e}")
            raise MemoryToolError(f"记忆对话失败: {str(e)}")


# 便捷函数接口
async def memory_chat(
    message: str,
    memorizing: bool = DEFAULT_MEMORIZING,
    image_uris: Optional[List[str]] = None,
    user_id: Optional[str] = None,
    ai_model: Optional[str] = None,
    mirix_adapter: Optional[MIRIXAdapter] = None
) -> Dict[str, Any]:
    """
    与 AI 进行基于记忆的个性化对话
    
    这是一个便捷函数，提供简单的接口来与 AI 进行个性化对话。
    支持自动记忆管理和多模态输入，提供连贯的对话体验。
    
    使用场景：
    - 需要个性化回应的日常对话
    - 获取基于个人记忆的个性化回应
    - 当需要 AI 学习和适应用户偏好时
    - 多轮对话中保持上下文连贯性
    
    执行顺序：
    - 可以独立使用，进行日常对话
    - 可以在 memory_search 后使用，提供更好的上下文
    - 通常与其他记忆工具结合使用，形成完整的记忆管理流程
    
    Args:
        message (str): 对话消息内容
            - 必填参数，用户要发送给 AI 的消息
            - 长度限制：1-10000 字符
            - 支持各种类型的对话内容
            - 示例："你好，今天天气怎么样？"、"帮我分析一下这个项目"
        
        memorizing (bool): 是否启用记忆化
            - 可选参数，默认值：True
            - True: 对话内容会被自动存储到记忆系统中
            - False: 对话内容不会被存储，适用于临时性对话
            - 建议在重要对话中设置为 True
        
        image_uris (Optional[List[str]]): 图像URI列表
            - 可选参数，用于多模态对话
            - 支持最多 10 个图像URI
            - URI 必须是有效的 HTTP/HTTPS 链接
            - 示例：["https://example.com/image1.jpg", "https://example.com/image2.png"]
        
        user_id (Optional[str]): 用户ID
            - 可选参数，如果未提供将使用默认用户ID
            - 用于指定对话的用户身份
        
        ai_model (Optional[str]): AI模型名称
            - 可选参数，指定使用的 AI 模型
            - 如果未提供将使用系统默认模型
            - 示例："gpt-4", "claude-3"
        
        mirix_adapter (Optional[MIRIXAdapter]): MIRIX 适配器实例
            - 可选参数，如果未提供将创建新实例
            - 用于与 MIRIX 后端通信
    
    Returns:
        Dict[str, Any]: 对话结果字典，包含以下字段：
            - success (bool): 操作是否成功
            - response (str): AI 的回复内容
            - memorized (bool): 是否已存储到记忆中
            - memory_updates (List[Dict]): 记忆更新列表，每个更新包含：
              * action: 操作类型（add, update, delete）
              * memory_type: 记忆类型
              * content_preview: 内容预览
              * memory_id: 记忆ID
            - chat_metadata (Dict): 对话元数据，包含：
              * message_length: 消息长度
              * response_length: 回复长度
              * memory_updates_count: 记忆更新数量
              * has_multimodal_input: 是否包含多模态输入
    
    Raises:
        MemoryToolError: 对话操作失败时抛出
        ValidationError: 参数验证失败时抛出
        MIRIXClientError: MIRIX 客户端通信失败时抛出
    
    Examples:
        # 基本对话
        result = await memory_chat("你好，今天天气怎么样？")
        
        # 不记忆的临时对话
        result = await memory_chat(
            "这是一个测试消息",
            memorizing=False
        )
        
        # 多模态对话（包含图像）
        result = await memory_chat(
            "请分析这张图片",
            image_uris=["https://example.com/image.jpg"]
        )
        
        # 指定AI模型的对话
        result = await memory_chat(
            "帮我写一段代码",
            ai_model="gpt-4"
        )
        
        # 检查对话结果
        if result["success"]:
            print(f"AI回复: {result['response']}")
            if result["memorized"]:
                print(f"已存储到记忆，更新了 {len(result['memory_updates'])} 条记忆")
        else:
            print(f"对话失败: {result.get('error', '未知错误')}")
    """
    # 创建或使用提供的适配器
    if mirix_adapter is None:
        from ..config import get_config
        mirix_adapter = MIRIXAdapter(get_config())
    
    # 创建对话工具实例
    chat_tool = MemoryChatTool(mirix_adapter)
    
    # 执行对话
    return await chat_tool.send_chat_message(
        message, memorizing, image_uris, user_id, ai_model
    )


# 工具元数据，用于 MCP 工具注册
TOOL_METADATA = {
    "name": "memory_chat",
    "description": "与 AI 进行基于记忆的个性化对话",
    "inputSchema": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "对话消息内容"
            },
            "memorizing": {
                "type": "boolean",
                "description": "是否启用记忆化（默认：True）",
                "default": DEFAULT_MEMORIZING
            },
            "image_uris": {
                "type": "array",
                "items": {"type": "string"},
                "description": "图像URI列表（可选，用于多模态对话）"
            }
        },
        "required": ["message"]
    },
    "returns": {
        "type": "object",
        "description": "对话结果，包含AI回复和记忆更新信息"
    },
    "examples": [
        {
            "description": "基本个性化对话",
            "parameters": {
                "message": "你好，今天天气怎么样？"
            }
        },
        {
            "description": "不记忆的临时对话",
            "parameters": {
                "message": "这是一个测试消息",
                "memorizing": False
            }
        },
        {
            "description": "多模态对话",
            "parameters": {
                "message": "请分析这张图片",
                "image_uris": ["https://example.com/image.jpg"]
            }
        }
    ]
}