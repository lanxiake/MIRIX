"""
MCP Server 异常处理模块

该模块定义了 MCP 服务器运行过程中可能遇到的各种异常类型，
提供统一的错误处理机制，便于错误追踪和调试。

异常层次结构：
- MCPServerError (基础异常)
  - ConfigurationError (配置相关错误)
  - MIRIXClientError (MIRIX 客户端错误)
    - ConnectionError (连接错误)
    - AuthenticationError (认证错误)
    - APIError (API 调用错误)
  - ToolError (工具执行错误)
    - MemoryToolError (记忆工具错误)
    - ValidationError (数据验证错误)
  - TransportError (传输层错误)
"""

from typing import Optional, Dict, Any
import traceback


class MCPServerError(Exception):
    """
    MCP 服务器基础异常类
    
    所有 MCP 服务器相关异常的基类，提供统一的错误信息格式和处理机制。
    
    Attributes:
        message: 错误消息
        error_code: 错误代码，用于程序化处理
        details: 额外的错误详情
        original_exception: 原始异常对象（如果有）
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        初始化基础异常
        
        Args:
            message: 错误消息描述
            error_code: 错误代码，便于程序化处理
            details: 包含额外错误信息的字典
            original_exception: 导致此异常的原始异常
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.original_exception = original_exception
        
        # 如果有原始异常，保存其堆栈跟踪
        if original_exception:
            self.details['original_traceback'] = traceback.format_exception(
                type(original_exception), 
                original_exception, 
                original_exception.__traceback__
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将异常转换为字典格式，便于序列化和日志记录
        
        Returns:
            包含异常信息的字典
        """
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details
        }


class ConfigurationError(MCPServerError):
    """
    配置相关错误
    
    当服务器配置文件缺失、格式错误或包含无效值时抛出此异常。
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        """
        初始化配置错误
        
        Args:
            message: 错误消息
            config_key: 出错的配置项键名
            **kwargs: 传递给基类的其他参数
        """
        details = kwargs.get('details', {})
        if config_key:
            details['config_key'] = config_key
        kwargs['details'] = details
        super().__init__(message, **kwargs)


class MIRIXClientError(MCPServerError):
    """
    MIRIX 客户端相关错误的基类
    
    当与 MIRIX 后端系统通信时发生错误时抛出此类异常。
    """
    pass


class ConnectionError(MIRIXClientError):
    """
    连接错误
    
    当无法建立与 MIRIX 后端的连接时抛出此异常。
    """
    
    def __init__(self, message: str, endpoint: Optional[str] = None, **kwargs):
        """
        初始化连接错误
        
        Args:
            message: 错误消息
            endpoint: 连接失败的端点地址
            **kwargs: 传递给基类的其他参数
        """
        details = kwargs.get('details', {})
        if endpoint:
            details['endpoint'] = endpoint
        kwargs['details'] = details
        super().__init__(message, **kwargs)


class AuthenticationError(MIRIXClientError):
    """
    认证错误
    
    当 MIRIX 后端认证失败时抛出此异常。
    """
    pass


class APIError(MIRIXClientError):
    """
    API 调用错误
    
    当 MIRIX API 返回错误响应时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        初始化 API 错误
        
        Args:
            message: 错误消息
            status_code: HTTP 状态码
            response_data: API 响应数据
            **kwargs: 传递给基类的其他参数
        """
        details = kwargs.get('details', {})
        if status_code:
            details['status_code'] = status_code
        if response_data:
            details['response_data'] = response_data
        kwargs['details'] = details
        super().__init__(message, **kwargs)


class ToolError(MCPServerError):
    """
    工具执行错误的基类
    
    当 MCP 工具执行过程中发生错误时抛出此类异常。
    """
    
    def __init__(self, message: str, tool_name: Optional[str] = None, **kwargs):
        """
        初始化工具错误
        
        Args:
            message: 错误消息
            tool_name: 出错的工具名称
            **kwargs: 传递给基类的其他参数
        """
        details = kwargs.get('details', {})
        if tool_name:
            details['tool_name'] = tool_name
        kwargs['details'] = details
        super().__init__(message, **kwargs)


class MemoryToolError(ToolError):
    """
    记忆工具相关错误
    
    当记忆管理工具执行失败时抛出此异常。
    """
    pass


class ValidationError(ToolError):
    """
    数据验证错误
    
    当工具输入参数验证失败时抛出此异常。
    """
    
    def __init__(
        self, 
        message: str, 
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        **kwargs
    ):
        """
        初始化验证错误
        
        Args:
            message: 错误消息
            field_name: 验证失败的字段名
            field_value: 验证失败的字段值
            **kwargs: 传递给基类的其他参数
        """
        details = kwargs.get('details', {})
        if field_name:
            details['field_name'] = field_name
        if field_value is not None:
            details['field_value'] = field_value
        kwargs['details'] = details
        super().__init__(message, **kwargs)


class ToolExecutionError(ToolError):
    """
    工具执行错误
    
    当工具执行过程中发生错误时抛出此异常。
    """
    pass


class TransportError(MCPServerError):
    """
    传输层错误
    
    当 MCP 传输层（stdio 或 SSE）发生错误时抛出此异常。
    """
    
    def __init__(self, message: str, transport_type: Optional[str] = None, **kwargs):
        """
        初始化传输错误
        
        Args:
            message: 错误消息
            transport_type: 传输类型（stdio 或 sse）
            **kwargs: 传递给基类的其他参数
        """
        details = kwargs.get('details', {})
        if transport_type:
            details['transport_type'] = transport_type
        kwargs['details'] = details
        super().__init__(message, **kwargs)


# 异常处理工具函数

def handle_exception(
    exception: Exception, 
    context: Optional[str] = None,
    reraise_as: Optional[type] = None
) -> None:
    """
    统一异常处理函数
    
    提供统一的异常处理逻辑，包括日志记录和异常转换。
    
    Args:
        exception: 要处理的异常
        context: 异常发生的上下文信息
        reraise_as: 要重新抛出的异常类型
        
    Raises:
        reraise_as: 如果指定了 reraise_as，则抛出该类型的异常
        Exception: 如果未指定 reraise_as，则重新抛出原异常
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 构建错误消息
    error_msg = str(exception)
    if context:
        error_msg = f"{context}: {error_msg}"
    
    # 记录异常日志
    logger.error(error_msg, exc_info=True)
    
    # 如果指定了重新抛出的异常类型
    if reraise_as:
        if issubclass(reraise_as, MCPServerError):
            raise reraise_as(
                message=error_msg,
                original_exception=exception
            )
        else:
            raise reraise_as(error_msg) from exception
    
    # 否则重新抛出原异常
    raise exception


def create_error_response(exception: Exception) -> Dict[str, Any]:
    """
    创建标准化的错误响应
    
    将异常转换为标准化的错误响应格式，用于 API 返回。
    
    Args:
        exception: 要转换的异常
        
    Returns:
        标准化的错误响应字典
    """
    if isinstance(exception, MCPServerError):
        return {
            'success': False,
            'error': exception.to_dict()
        }
    else:
        return {
            'success': False,
            'error': {
                'error_type': type(exception).__name__,
                'error_code': 'UNKNOWN_ERROR',
                'message': str(exception),
                'details': {}
            }
        }