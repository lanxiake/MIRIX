"""
MCP Server 工具模块

该模块提供 MCP 服务器运行所需的各种工具函数和辅助功能，
包括日志配置、数据验证、类型转换、重试机制等通用功能。

主要功能：
1. 日志配置和管理
2. 数据验证和类型转换
3. 重试机制和错误处理
4. 时间和日期处理
5. 字符串和数据格式化
6. 异步操作辅助函数
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from pathlib import Path
import hashlib
import uuid

from .exceptions import ValidationError, MCPServerError

# 类型变量定义
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


# 日志配置相关函数

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    配置日志系统
    
    设置统一的日志格式和输出方式，支持控制台和文件输出。
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，如果为 None 则只输出到控制台
        format_string: 自定义日志格式字符串
        
    Returns:
        配置好的 logger 实例
    """
    # 默认日志格式
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    
    # 创建格式化器
    formatter = logging.Formatter(format_string)
    
    # 获取根日志器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称，通常使用模块的 __name__
        
    Returns:
        日志器实例
    """
    return logging.getLogger(name)


# 数据验证和类型转换函数

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    验证必需字段是否存在
    
    Args:
        data: 要验证的数据字典
        required_fields: 必需字段列表
        
    Raises:
        ValidationError: 当必需字段缺失时
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(
            f"缺少必需字段: {', '.join(missing_fields)}",
            details={'missing_fields': missing_fields}
        )


def validate_field_type(
    value: Any, 
    expected_type: type, 
    field_name: str,
    allow_none: bool = False
) -> None:
    """
    验证字段类型
    
    Args:
        value: 要验证的值
        expected_type: 期望的类型
        field_name: 字段名称
        allow_none: 是否允许 None 值
        
    Raises:
        ValidationError: 当类型不匹配时
    """
    if value is None and allow_none:
        return
    
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"字段 '{field_name}' 类型错误，期望 {expected_type.__name__}，实际 {type(value).__name__}",
            field_name=field_name,
            field_value=value,
            details={
                'expected_type': expected_type.__name__,
                'actual_type': type(value).__name__
            }
        )


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    安全的 JSON 解析
    
    Args:
        json_str: JSON 字符串
        default: 解析失败时的默认值
        
    Returns:
        解析后的对象或默认值
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    安全的 JSON 序列化
    
    Args:
        obj: 要序列化的对象
        default: 序列化失败时的默认值
        
    Returns:
        JSON 字符串或默认值
    """
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return default


# 重试机制和错误处理

def retry_async(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    异步函数重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 延迟时间递增因子
        exceptions: 需要重试的异常类型元组
        
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger = get_logger(__name__)
                        logger.warning(
                            f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}，"
                            f"{current_delay:.1f}秒后重试"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"函数 {func.__name__} 重试 {max_attempts} 次后仍然失败")
            
            # 如果所有重试都失败，抛出最后一个异常
            raise last_exception
        
        return wrapper
    return decorator


def retry_sync(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    同步函数重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 延迟时间递增因子
        exceptions: 需要重试的异常类型元组
        
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger = get_logger(__name__)
                        logger.warning(
                            f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}，"
                            f"{current_delay:.1f}秒后重试"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"函数 {func.__name__} 重试 {max_attempts} 次后仍然失败")
            
            # 如果所有重试都失败，抛出最后一个异常
            raise last_exception
        
        return wrapper
    return decorator


# 时间和日期处理函数

def get_current_timestamp() -> float:
    """
    获取当前时间戳
    
    Returns:
        当前时间戳（秒）
    """
    return time.time()


def get_current_iso_time() -> str:
    """
    获取当前 ISO 格式时间字符串
    
    Returns:
        ISO 格式的时间字符串
    """
    return datetime.now(timezone.utc).isoformat()


def format_timestamp(timestamp: float, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化时间戳
    
    Args:
        timestamp: 时间戳
        format_str: 格式字符串
        
    Returns:
        格式化后的时间字符串
    """
    return datetime.fromtimestamp(timestamp).strftime(format_str)


# 字符串和数据格式化函数

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断字符串
    
    Args:
        text: 要截断的字符串
        max_length: 最大长度
        suffix: 截断后的后缀
        
    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    import re
    # 移除或替换不安全字符
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除控制字符
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    # 限制长度
    return truncate_string(sanitized, 255, "")


def generate_unique_id() -> str:
    """
    生成唯一标识符
    
    Returns:
        UUID 字符串
    """
    return str(uuid.uuid4())


def generate_hash(data: str, algorithm: str = "sha256") -> str:
    """
    生成数据哈希值
    
    Args:
        data: 要哈希的数据
        algorithm: 哈希算法 (md5, sha1, sha256, sha512)
        
    Returns:
        哈希值字符串
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(data.encode('utf-8'))
    return hash_obj.hexdigest()


# 异步操作辅助函数

async def run_with_timeout(
    coro, 
    timeout: float,
    timeout_message: str = "操作超时"
) -> Any:
    """
    带超时的异步操作执行
    
    Args:
        coro: 协程对象
        timeout: 超时时间（秒）
        timeout_message: 超时错误消息
        
    Returns:
        协程执行结果
        
    Raises:
        MCPServerError: 当操作超时时
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise MCPServerError(
            timeout_message,
            error_code="TIMEOUT_ERROR",
            details={'timeout': timeout}
        )


async def gather_with_concurrency(
    *coroutines,
    max_concurrency: int = 10,
    return_exceptions: bool = False
) -> List[Any]:
    """
    限制并发数的 gather 操作
    
    Args:
        *coroutines: 协程列表
        max_concurrency: 最大并发数
        return_exceptions: 是否返回异常而不是抛出
        
    Returns:
        结果列表
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def run_with_semaphore(coro):
        async with semaphore:
            return await coro
    
    limited_coroutines = [run_with_semaphore(coro) for coro in coroutines]
    return await asyncio.gather(*limited_coroutines, return_exceptions=return_exceptions)


# 配置和环境相关函数

def load_env_var(
    var_name: str, 
    default: Optional[str] = None,
    required: bool = False,
    var_type: type = str
) -> Any:
    """
    加载环境变量
    
    Args:
        var_name: 环境变量名
        default: 默认值
        required: 是否必需
        var_type: 变量类型
        
    Returns:
        环境变量值
        
    Raises:
        ValidationError: 当必需的环境变量不存在时
    """
    import os
    
    value = os.getenv(var_name, default)
    
    if required and value is None:
        raise ValidationError(
            f"必需的环境变量 '{var_name}' 未设置",
            field_name=var_name
        )
    
    if value is None:
        return None
    
    # 类型转换
    try:
        if var_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif var_type == int:
            return int(value)
        elif var_type == float:
            return float(value)
        else:
            return var_type(value)
    except (ValueError, TypeError) as e:
        raise ValidationError(
            f"环境变量 '{var_name}' 类型转换失败: {e}",
            field_name=var_name,
            field_value=value,
            original_exception=e
        )


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        Path 对象
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


# 数据结构辅助函数

def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    深度合并两个字典
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
        
    Returns:
        合并后的字典
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(
    d: Dict[str, Any], 
    parent_key: str = '', 
    sep: str = '.'
) -> Dict[str, Any]:
    """
    扁平化嵌套字典
    
    Args:
        d: 要扁平化的字典
        parent_key: 父键名
        sep: 键名分隔符
        
    Returns:
        扁平化后的字典
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


# 性能监控和调试函数

def measure_time(func: F) -> F:
    """
    测量函数执行时间的装饰器
    
    Args:
        func: 要测量的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            logger = get_logger(__name__)
            logger.debug(f"函数 {func.__name__} 执行时间: {end_time - start_time:.4f}秒")
    
    return wrapper


def measure_time_async(func: F) -> F:
    """
    测量异步函数执行时间的装饰器
    
    Args:
        func: 要测量的异步函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            logger = get_logger(__name__)
            logger.debug(f"异步函数 {func.__name__} 执行时间: {end_time - start_time:.4f}秒")
    
    return wrapper