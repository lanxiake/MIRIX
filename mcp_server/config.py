"""
MCP Server 配置管理 - 纯SSE模式

基于 Pydantic Settings 的配置管理，专注于 SSE 模式的 MCP 服务器。
支持环境变量和 .env 文件配置。
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class MCPServerConfig(BaseSettings):
    """MCP 服务器配置 - 纯SSE模式
    
    专门为SSE模式优化的配置管理，移除了stdio相关配置。
    """
    
    # 服务器基本信息
    server_name: str = Field(
        default="MIRIX MCP Server",
        env="MCP_SERVER_NAME",
        description="MCP 服务器名称"
    )
    server_version: str = Field(
        default="2.0.0",
        env="MCP_SERVER_VERSION",
        description="MCP 服务器版本"
    )
    
    # 传输配置 - 固定为SSE模式
    transport_type: str = Field(
        default="sse",
        env="MCP_TRANSPORT_TYPE",
        description="传输方式：固定为 sse"
    )
    
    # SSE 传输配置
    sse_host: str = Field(
        default="0.0.0.0",
        env="MCP_SSE_HOST",
        description="SSE 服务器监听地址"
    )
    sse_port: int = Field(
        default=18002,
        env="MCP_SSE_PORT",
        description="SSE 服务器监听端口"
    )
    sse_heartbeat_interval: int = Field(
        default=30,
        env="MCP_SSE_HEARTBEAT_INTERVAL",
        description="SSE 心跳间隔（秒）"
    )
    sse_endpoint: str = Field(
        default="/sse",
        env="MCP_SSE_ENDPOINT",
        description="SSE 连接端点路径"
    )
    sse_message_endpoint: str = Field(
        default="/messages",
        env="MCP_SSE_MESSAGE_ENDPOINT",
        description="SSE 消息端点路径"
    )
    sse_cors_origins: List[str] = Field(
        default=["*"],
        env="MCP_SSE_CORS_ORIGINS",
        description="允许的CORS源"
    )
    
    # MIRIX 后端集成配置
    mirix_backend_url: str = Field(
        default="http://mirix-backend:47283",
        env="MIRIX_BACKEND_URL",
        description="MIRIX 后端服务 URL"
    )
    mirix_backend_timeout: int = Field(
        default=30,
        env="MIRIX_BACKEND_TIMEOUT",
        description="MIRIX 后端请求超时时间（秒）"
    )
    
    # 记忆管理配置
    default_user_id: str = Field(
        default="default_user",
        env="MCP_DEFAULT_USER_ID",
        description="默认用户 ID"
    )
    memory_search_limit: int = Field(
        default=10,
        env="MCP_MEMORY_SEARCH_LIMIT",
        description="记忆搜索结果限制数量"
    )
    
    # 日志配置
    log_level: str = Field(
        default="INFO",
        env="MCP_LOG_LEVEL",
        description="日志级别"
    )
    debug: bool = Field(
        default=False,
        env="MCP_DEBUG",
        description="调试模式"
    )
    
    # MCP 协议配置
    mcp_version: str = Field(
        default="2024-11-05",
        env="MCP_VERSION",
        description="MCP 协议版本"
    )
    
    # 性能配置
    max_concurrent_requests: int = Field(
        default=100,
        env="MCP_MAX_CONCURRENT_REQUESTS",
        description="最大并发请求数"
    )
    request_timeout: int = Field(
        default=60,
        env="MCP_REQUEST_TIMEOUT",
        description="请求超时时间（秒）"
    )
    
    @validator("transport_type")
    def validate_transport_type(cls, v):
        """验证传输类型 - 必须为sse"""
        if v != "sse":
            # 强制设置为sse，确保兼容性
            return "sse"
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level 必须是以下之一: {valid_levels}")
        return v.upper()
    
    @validator("mirix_backend_url")
    def validate_backend_url(cls, v):
        """验证后端 URL 格式"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("mirix_backend_url 必须以 http:// 或 https:// 开头")
        return v
    
    @validator("sse_port")
    def validate_sse_port(cls, v):
        """验证SSE端口范围"""
        if not (1 <= v <= 65535):
            raise ValueError("sse_port 必须在 1-65535 范围内")
        return v
    
    @validator("sse_endpoint")
    def validate_sse_endpoint(cls, v):
        """验证SSE端点路径"""
        if not v.startswith("/"):
            v = "/" + v
        return v
    
    class Config:
        """Pydantic 配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 忽略额外的字段


# 全局配置实例
_config: Optional[MCPServerConfig] = None


def get_config(config_path: Optional[str] = None) -> MCPServerConfig:
    """获取全局配置实例
    
    Args:
        config_path: 可选的配置文件路径
    
    Returns:
        MCPServerConfig: 配置实例
    """
    global _config
    if _config is None:
        if config_path:
            # 如果指定了配置文件路径，设置环境变量
            os.environ["MCP_CONFIG_FILE"] = str(config_path)
        _config = MCPServerConfig()
    return _config


def reload_config() -> MCPServerConfig:
    """重新加载配置
    
    Returns:
        MCPServerConfig: 新的配置实例
    """
    global _config
    _config = MCPServerConfig()
    return _config