"""
简化的 MCP 服务器配置

不依赖 pydantic-settings 的简单配置管理，专门为标准 MCP 服务器设计。
"""

import os
from typing import Optional


class MCPServerSettings:
    """MCP 服务器配置"""

    def __init__(self, custom_backend_url: str = None, custom_user_id: str = None):
        # MIRIX 后端配置 - 支持自定义 URL
        if custom_backend_url:
            self.mirix_backend_url = custom_backend_url
        else:
            self.mirix_backend_url = os.getenv("MIRIX_BACKEND_URL", "http://localhost:47283")

        self.mirix_backend_timeout = int(os.getenv("MIRIX_BACKEND_TIMEOUT", "30"))

        # 记忆管理配置 - 支持自定义用户 ID
        if custom_user_id:
            self.default_user_id = custom_user_id
        else:
            self.default_user_id = os.getenv("DEFAULT_USER_ID", "default_user")

        self.ai_model = os.getenv("AI_MODEL", "gemini-2.0-flash-thinking-exp")
        self.auto_categorize_memory = os.getenv("AUTO_CATEGORIZE_MEMORY", "true").lower() == "true"
        self.default_memory_type = os.getenv("DEFAULT_MEMORY_TYPE", "semantic")
        self.memory_search_limit = int(os.getenv("MEMORY_SEARCH_LIMIT", "10"))

        # SSE 服务器配置
        self.sse_host = os.getenv("SSE_HOST", "localhost")
        self.sse_port = int(os.getenv("SSE_PORT", "8080"))
        self.sse_enabled = os.getenv("SSE_ENABLED", "false").lower() == "true"

        # 调试配置
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        # 验证配置
        self._validate()

    def _validate(self):
        """验证配置"""
        # 验证后端URL
        if not self.mirix_backend_url.startswith(("http://", "https://")):
            raise ValueError("MIRIX backend URL must start with http:// or https://")
        self.mirix_backend_url = self.mirix_backend_url.rstrip("/")

        # 验证日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            raise ValueError(f"Invalid log level: {self.log_level}. Must be one of {valid_levels}")


# 全局设置实例
_settings: Optional[MCPServerSettings] = None


def get_settings(custom_backend_url: str = None, custom_user_id: str = None) -> MCPServerSettings:
    """获取配置实例（单例模式）"""
    global _settings
    if _settings is None:
        _settings = MCPServerSettings(custom_backend_url, custom_user_id)
    return _settings


def reload_settings(custom_backend_url: str = None, custom_user_id: str = None) -> MCPServerSettings:
    """重新加载配置"""
    global _settings
    _settings = MCPServerSettings(custom_backend_url, custom_user_id)
    return _settings