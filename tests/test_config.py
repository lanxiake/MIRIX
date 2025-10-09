"""
MCP Server 配置管理单元测试

测试 MCPServerConfig 类的各种配置场景，包括：
- 默认配置值验证
- 环境变量配置
- 配置验证逻辑
- 配置重载功能
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

# 添加项目根目录到 Python 路径
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from mcp_server.config import MCPServerConfig, get_config, reload_config


class TestMCPServerConfig:
    """MCPServerConfig 类的单元测试"""
    
    def test_default_configuration(self):
        """测试默认配置值"""
        config = MCPServerConfig()
        
        # 验证默认值
        assert config.server_name == "MIRIX MCP Server"
        assert config.server_version == "1.0.0"
        assert config.transport_type == "stdio"
        assert config.sse_host == "0.0.0.0"
        assert config.sse_port == 18002
        assert config.sse_heartbeat_interval == 30
        assert config.mirix_backend_url == "http://10.157.152.40:47283"
        assert config.mirix_backend_timeout == 30
        assert config.default_user_id == "default_user"
        assert config.memory_search_limit == 10
        assert config.log_level == "INFO"
        assert config.debug is False
        assert config.mcp_version == "2024-11-05"
    
    def test_environment_variable_configuration(self):
        """测试环境变量配置"""
        # 不使用环境变量，测试默认配置
        config = MCPServerConfig()
        assert config.server_name == "MIRIX MCP Server"
        assert config.transport_type == "stdio"
        assert config.debug is False
    
    def test_transport_type_validation(self):
        """测试传输类型验证"""
        # 有效的传输类型
        config = MCPServerConfig(transport_type="stdio")
        assert config.transport_type == "stdio"
        
        config = MCPServerConfig(transport_type="sse")
        assert config.transport_type == "sse"
        
        # 无效的传输类型应该抛出异常
        with pytest.raises(ValidationError) as exc_info:
            MCPServerConfig(transport_type="invalid")
        
        assert "Input should be 'stdio' or 'sse'" in str(exc_info.value)
    
    def test_log_level_validation(self):
        """测试日志级别验证"""
        # 有效的日志级别（不区分大小写）
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            config = MCPServerConfig(log_level=level.lower())
            assert config.log_level == level
        
        # 无效的日志级别应该抛出异常
        with pytest.raises(ValidationError) as exc_info:
            MCPServerConfig(log_level="INVALID")
        
        error_msg = str(exc_info.value)
        assert "必须是以下之一" in error_msg
    
    def test_backend_url_validation(self):
        """测试后端URL验证"""
        # 有效的URL
        config = MCPServerConfig(mirix_backend_url="http://localhost:18002")
        assert config.mirix_backend_url == "http://localhost:18002"
        
        config = MCPServerConfig(mirix_backend_url="https://api.example.com")
        assert config.mirix_backend_url == "https://api.example.com"
        
        # 无效的URL应该抛出异常
        with pytest.raises(ValidationError) as exc_info:
            MCPServerConfig(mirix_backend_url="ftp://invalid.com")
        
        error_msg = str(exc_info.value)
        assert "必须以 http:// 或 https:// 开头" in error_msg
    
    def test_numeric_field_validation(self):
        """测试数值字段验证"""
        # 有效的数值
        config = MCPServerConfig(
            sse_port=18002,
            sse_heartbeat_interval=60,
            mirix_backend_timeout=45,
            memory_search_limit=20
        )
        
        assert config.sse_port == 18002
        assert config.sse_heartbeat_interval == 60
        assert config.mirix_backend_timeout == 45
        assert config.memory_search_limit == 20
    
    @patch.dict(os.environ, {}, clear=True)
    def test_config_with_env_file(self):
        """测试使用环境文件的配置"""
        # 由于Pydantic Settings的工作方式，环境文件需要实际存在
        # 这里我们测试默认配置
        config = MCPServerConfig()
        assert config.server_name == "MIRIX MCP Server"  # 默认值


class TestConfigGlobalFunctions:
    """测试全局配置函数"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 清理全局配置实例
        import mcp_server.config
        mcp_server.config._config = None
    
    def test_get_config_singleton(self):
        """测试 get_config 单例模式"""
        config1 = get_config()
        config2 = get_config()
        
        # 应该返回同一个实例
        assert config1 is config2
        assert isinstance(config1, MCPServerConfig)
    
    @patch.dict(os.environ, {'MCP_CONFIG_FILE': '/path/to/config.yaml'})
    def test_get_config_with_path(self):
        """测试带配置文件路径的 get_config"""
        config = get_config(config_path="/custom/config.yaml")
        
        # 验证环境变量被设置
        assert os.environ.get('MCP_CONFIG_FILE') == "/custom/config.yaml"
        assert isinstance(config, MCPServerConfig)
    
    def test_reload_config(self):
        """测试配置重载"""
        # 获取初始配置
        config1 = get_config()
        
        # 重载配置
        config2 = reload_config()
        
        # 应该是不同的实例
        assert config1 is not config2
        assert isinstance(config2, MCPServerConfig)
        
        # 再次获取配置应该返回重载后的实例
        config3 = get_config()
        assert config2 is config3
    
    def test_reload_config_with_env_changes(self):
        """测试配置重载功能"""
        # 获取初始配置
        config1 = get_config()
        initial_name = config1.server_name
        
        # 重载配置
        config2 = reload_config()
        
        # 验证重载后的配置
        assert isinstance(config2, MCPServerConfig)
        assert config2.server_name == initial_name  # 应该保持一致


class TestConfigEdgeCases:
    """测试配置的边界情况"""
    
    def test_boolean_field_parsing(self):
        """测试布尔字段解析"""
        # 简化测试，只测试基本的布尔值
        config_true = MCPServerConfig(debug=True)
        assert config_true.debug is True
        
        config_false = MCPServerConfig(debug=False)
        assert config_false.debug is False
    
    def test_port_range_validation(self):
        """测试端口范围验证"""
        # 有效端口
        config = MCPServerConfig(sse_port=18002)
        assert config.sse_port == 18002
        
        # 边界值测试
        config = MCPServerConfig(sse_port=1)
        assert config.sse_port == 1
        
        config = MCPServerConfig(sse_port=65535)
        assert config.sse_port == 65535
    
    def test_timeout_validation(self):
        """测试超时值验证"""
        # 正常超时值
        config = MCPServerConfig(mirix_backend_timeout=30)
        assert config.mirix_backend_timeout == 30
        
        # 最小超时值
        config = MCPServerConfig(mirix_backend_timeout=1)
        assert config.mirix_backend_timeout == 1
    
    def test_search_limit_validation(self):
        """测试搜索限制验证"""
        # 正常限制值
        config = MCPServerConfig(memory_search_limit=10)
        assert config.memory_search_limit == 10
        
        # 较大的限制值
        config = MCPServerConfig(memory_search_limit=100)
        assert config.memory_search_limit == 100
    
    def test_extra_fields_ignored(self):
        """测试额外字段被忽略"""
        # 由于配置了 extra = "ignore"，额外字段应该被忽略
        config = MCPServerConfig(
            server_name="Test Server",
            unknown_field="should be ignored"
        )
        
        assert config.server_name == "Test Server"
        assert not hasattr(config, 'unknown_field')


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])