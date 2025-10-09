"""
自定义模型配置相关的数据模型和验证逻辑

该模块定义了自定义模型配置管理所需的所有Pydantic模型，
包括请求、响应和验证逻辑，确保数据的一致性和安全性。
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, Dict, Any, List
import re
from pathlib import Path


class CustomModelDetailResponse(BaseModel):
    """
    自定义模型详情响应模型
    
    用于返回单个自定义模型的完整配置信息，
    主要用于编辑时预填充表单数据。
    """
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    model_config: Optional[Dict[str, Any]] = Field(None, description="模型配置数据")


class UpdateCustomModelRequest(BaseModel):
    """
    更新自定义模型请求模型
    
    包含更新自定义模型配置所需的所有字段，
    并提供完整的数据验证逻辑。
    """
    model_name: str = Field(..., description="模型名称，用于标识模型")
    model_endpoint: str = Field(..., description="模型API端点URL")
    api_key: str = Field(..., description="API访问密钥")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="生成温度，控制随机性")
    max_tokens: int = Field(4096, gt=0, description="最大生成token数量")
    maximum_length: int = Field(32768, gt=0, description="最大上下文长度")

    @validator('model_name')
    def validate_model_name(cls, v):
        """
        验证模型名称的有效性
        
        规则：
        1. 不能为空或只包含空白字符
        2. 只能包含字母、数字、下划线和连字符
        3. 长度限制在1-50个字符之间
        """
        if not v or not v.strip():
            raise ValueError('模型名称不能为空')
        
        v = v.strip()
        if len(v) > 50:
            raise ValueError('模型名称长度不能超过50个字符')
            
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('模型名称只能包含字母、数字、下划线和连字符')
        
        return v

    @validator('model_endpoint')
    def validate_endpoint(cls, v):
        """
        验证模型端点URL的有效性
        
        规则：
        1. 不能为空
        2. 必须是有效的HTTP/HTTPS URL
        3. 不能包含危险字符
        """
        if not v or not v.strip():
            raise ValueError('模型端点不能为空')
        
        v = v.strip()
        if not v.startswith(('http://', 'https://')):
            raise ValueError('模型端点必须是有效的HTTP/HTTPS URL')
        
        # 基本的URL安全检查
        dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        if any(char in v for char in dangerous_chars):
            raise ValueError('模型端点包含非法字符')
        
        return v

    @validator('api_key')
    def validate_api_key(cls, v):
        """
        验证API密钥的基本格式
        
        规则：
        1. 不能为空（除非是本地服务）
        2. 长度合理（通常在10-200字符之间）
        3. 不包含明显的非法字符
        """
        if not v:
            # API密钥可以为空，用于本地服务
            return v
        
        v = v.strip()
        if len(v) < 10:
            raise ValueError('API密钥长度过短，请检查是否正确')
        
        if len(v) > 200:
            raise ValueError('API密钥长度过长，请检查是否正确')
        
        return v

    @validator('temperature')
    def validate_temperature(cls, v):
        """
        验证温度参数的有效性
        
        温度值必须在0-2之间，控制生成的随机性
        """
        if not 0 <= v <= 2:
            raise ValueError('温度值必须在0-2之间')
        return v

    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        """
        验证最大token数的有效性
        
        必须是正整数，且不能超过合理范围
        """
        if v <= 0:
            raise ValueError('最大tokens必须大于0')
        
        if v > 100000:  # 设置一个合理的上限
            raise ValueError('最大tokens不能超过100000')
        
        return v

    @validator('maximum_length')
    def validate_maximum_length(cls, v):
        """
        验证最大上下文长度的有效性
        
        必须是正整数，且通常应该大于max_tokens
        """
        if v <= 0:
            raise ValueError('最大上下文长度必须大于0')
        
        if v > 1000000:  # 设置一个合理的上限
            raise ValueError('最大上下文长度不能超过1000000')
        
        return v

    @validator('maximum_length')
    def validate_length_consistency(cls, v, values):
        """
        验证上下文长度与最大token数的一致性
        
        上下文长度通常应该大于或等于最大token数
        """
        if 'max_tokens' in values and v < values['max_tokens']:
            raise ValueError('最大上下文长度应该大于或等于最大tokens数')
        
        return v


class UpdateCustomModelResponse(BaseModel):
    """
    更新自定义模型响应模型
    
    返回更新操作的结果，包括成功状态和相关信息
    """
    success: bool = Field(..., description="更新是否成功")
    message: str = Field(..., description="操作结果消息")
    old_model_id: Optional[str] = Field(None, description="原模型ID（如果名称改变）")
    new_model_id: Optional[str] = Field(None, description="新模型ID（如果名称改变）")


class DeleteCustomModelResponse(BaseModel):
    """
    删除自定义模型响应模型
    
    返回删除操作的结果和相关状态信息
    """
    success: bool = Field(..., description="删除是否成功")
    message: str = Field(..., description="操作结果消息")
    was_active: bool = Field(False, description="被删除的模型是否是当前使用的模型")


class ModelStatusResponse(BaseModel):
    """
    模型状态响应模型
    
    返回指定模型的使用状态信息，用于判断是否可以安全删除
    """
    success: bool = Field(..., description="查询是否成功")
    model_id: str = Field(..., description="模型标识符")
    is_active: bool = Field(False, description="是否是当前主模型")
    is_memory_model: bool = Field(False, description="是否是当前记忆模型")
    can_delete: bool = Field(True, description="是否可以安全删除")
    usage_info: str = Field("", description="使用状态描述信息")


class CustomModelConfig(BaseModel):
    """
    自定义模型配置数据模型
    
    用于内部处理和YAML文件的序列化/反序列化
    """
    agent_name: str = Field("mirix", description="代理名称")
    model_name: str = Field(..., description="模型名称")
    model_endpoint: str = Field(..., description="模型端点")
    api_key: Optional[str] = Field(None, description="API密钥")
    model_provider: str = Field("local_server", description="模型提供商")
    generation_config: Dict[str, Any] = Field(..., description="生成配置")

    @classmethod
    def from_request(cls, request: UpdateCustomModelRequest) -> 'CustomModelConfig':
        """
        从更新请求创建配置对象
        
        Args:
            request: 更新请求对象
            
        Returns:
            CustomModelConfig: 配置对象
        """
        return cls(
            model_name=request.model_name,
            model_endpoint=request.model_endpoint,
            api_key=request.api_key,
            generation_config={
                'temperature': request.temperature,
                'max_tokens': request.max_tokens,
                'context_window': request.maximum_length
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式，用于YAML序列化
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'agent_name': self.agent_name,
            'model_name': self.model_name,
            'model_endpoint': self.model_endpoint,
            'api_key': self.api_key,
            'model_provider': self.model_provider,
            'generation_config': self.generation_config
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomModelConfig':
        """
        从字典创建配置对象，用于YAML反序列化
        
        Args:
            data: 配置字典
            
        Returns:
            CustomModelConfig: 配置对象
        """
        return cls(**data)


class CustomModelListItem(BaseModel):
    """
    自定义模型列表项模型
    
    用于在模型列表中显示的简化信息
    """
    model_id: str = Field(..., description="模型标识符")
    model_name: str = Field(..., description="模型名称")
    model_endpoint: str = Field(..., description="模型端点")
    is_active: bool = Field(False, description="是否是当前使用的模型")
    is_memory_model: bool = Field(False, description="是否是记忆模型")
    created_at: Optional[str] = Field(None, description="创建时间")
    last_modified: Optional[str] = Field(None, description="最后修改时间")


class EnhancedListCustomModelsResponse(BaseModel):
    """
    增强的自定义模型列表响应
    
    包含更多状态信息的模型列表响应
    """
    success: bool = Field(True, description="查询是否成功")
    message: str = Field("", description="响应消息")
    models: List[CustomModelListItem] = Field([], description="模型列表")
    total_count: int = Field(0, description="模型总数")


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，确保文件系统安全
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的安全文件名
    """
    # 移除或替换危险字符
    safe_chars = re.sub(r'[^\w\-_.]', '_', filename)
    
    # 确保不以点开头（隐藏文件）
    if safe_chars.startswith('.'):
        safe_chars = 'model_' + safe_chars[1:]
    
    # 限制长度
    if len(safe_chars) > 50:
        safe_chars = safe_chars[:50]
    
    return safe_chars


def get_model_id_from_name(model_name: str) -> str:
    """
    从模型名称生成模型ID（文件名）
    
    Args:
        model_name: 模型名称
        
    Returns:
        str: 模型ID
    """
    return sanitize_filename(model_name)


def validate_custom_models_directory() -> Path:
    """
    验证并创建自定义模型配置目录
    
    Returns:
        Path: 自定义模型配置目录路径
        
    Raises:
        PermissionError: 如果没有权限创建目录
        OSError: 如果目录创建失败
    """
    custom_models_dir = Path.home() / ".mirix" / "custom_models"
    
    try:
        custom_models_dir.mkdir(parents=True, exist_ok=True)
        return custom_models_dir
    except PermissionError:
        raise PermissionError(f"没有权限创建目录: {custom_models_dir}")
    except OSError as e:
        raise OSError(f"创建目录失败: {custom_models_dir}, 错误: {e}")