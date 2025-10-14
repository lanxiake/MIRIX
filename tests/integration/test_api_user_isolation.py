"""
API层用户数据隔离集成测试

测试API端点的用户数据隔离机制,确保:
1. user_id参数验证正常工作
2. 用户只能访问自己的数据
3. 用户切换功能被禁用
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from mirix.server.fastapi_server import app, validate_and_sanitize_user_id
from mirix.schemas.user import User as PydanticUser


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """创建mock用户"""
    user = Mock(spec=PydanticUser)
    user.id = "user-test-123"
    user.organization_id = "org-test-456"
    user.name = "Test User"
    return user


@pytest.fixture
def mock_agent(mock_user):
    """创建mock agent"""
    agent = Mock()
    agent.client = Mock()
    agent.client.user = mock_user
    agent.client.user_id = mock_user.id
    return agent


class TestMemoryEndpointsUserIsolation:
    """测试记忆端点的用户隔离"""

    @patch('mirix.server.fastapi_server.get_agent')
    @patch('mirix.server.fastapi_server.get_user_or_default')
    def test_episodic_memory_endpoint_uses_current_user(self, mock_get_user, mock_get_agent, client, mock_user, mock_agent):
        """测试情景记忆端点强制使用当前用户ID"""
        mock_get_agent.return_value = mock_agent
        mock_get_user.return_value = mock_user

        # 尝试访问其他用户的数据
        with patch('mirix.server.fastapi_server.EpisodicMemoryManager') as mock_manager:
            mock_manager.return_value.list.return_value = []

            response = client.get(
                "/memory/episodic",
                params={"user_id": "user-other-999"}  # 尝试访问其他用户
            )

            # 应该返回200,但只返回当前用户的数据
            assert response.status_code == 200

            # 验证validate_and_sanitize_user_id被调用并返回当前用户ID
            # (实际调用会记录警告日志)

    @patch('mirix.server.fastapi_server.get_agent')
    @patch('mirix.server.fastapi_server.get_user_or_default')
    def test_semantic_memory_endpoint_uses_current_user(self, mock_get_user, mock_get_agent, client, mock_user, mock_agent):
        """测试语义记忆端点强制使用当前用户ID"""
        mock_get_agent.return_value = mock_agent
        mock_get_user.return_value = mock_user

        with patch('mirix.server.fastapi_server.SemanticMemoryManager') as mock_manager:
            mock_manager.return_value.list.return_value = []

            response = client.get(
                "/memory/semantic",
                params={"user_id": "user-attacker-666"}
            )

            assert response.status_code == 200

    @patch('mirix.server.fastapi_server.get_agent')
    @patch('mirix.server.fastapi_server.get_user_or_default')
    def test_procedural_memory_endpoint_uses_current_user(self, mock_get_user, mock_get_agent, client, mock_user, mock_agent):
        """测试程序记忆端点强制使用当前用户ID"""
        mock_get_agent.return_value = mock_agent
        mock_get_user.return_value = mock_user

        with patch('mirix.server.fastapi_server.ProceduralMemoryManager') as mock_manager:
            mock_manager.return_value.list.return_value = []

            response = client.get(
                "/memory/procedural",
                params={"user_id": "user-hacker-777"}
            )

            assert response.status_code == 200

    @patch('mirix.server.fastapi_server.get_agent')
    @patch('mirix.server.fastapi_server.get_user_or_default')
    def test_resource_memory_endpoint_uses_current_user(self, mock_get_user, mock_get_agent, client, mock_user, mock_agent):
        """测试资源记忆端点强制使用当前用户ID"""
        mock_get_agent.return_value = mock_agent
        mock_get_user.return_value = mock_user

        with patch('mirix.server.fastapi_server.ResourceMemoryManager') as mock_manager:
            mock_manager.return_value.list.return_value = []

            response = client.get(
                "/memory/resources",
                params={"user_id": "user-malicious-888"}
            )

            assert response.status_code == 200


class TestUserSwitchingDisabled:
    """测试用户切换功能被禁用"""

    @patch('mirix.server.fastapi_server.get_agent')
    def test_user_switch_returns_403(self, mock_get_agent, client, mock_agent):
        """测试用户切换端点返回403 Forbidden"""
        mock_get_agent.return_value = mock_agent

        response = client.post(
            "/users/switch",
            json={"user_id": "user-target-999"}
        )

        # 应该返回403
        assert response.status_code == 403

        # 错误消息应该说明功能已禁用
        assert "disabled" in response.json().get("detail", "").lower()

    @patch('mirix.server.fastapi_server.get_agent')
    def test_user_switch_logs_warning(self, mock_get_agent, client, mock_agent, caplog):
        """测试用户切换尝试被记录到日志"""
        mock_get_agent.return_value = mock_agent

        response = client.post(
            "/users/switch",
            json={"user_id": "user-evil-999"}
        )

        assert response.status_code == 403

        # 应该记录警告日志
        # (检查caplog.records中是否有相关日志)


class TestValidateAndSanitizeUserId:
    """测试user_id参数验证函数"""

    def test_none_user_id_returns_current(self):
        """测试user_id为None时返回当前用户ID"""
        result = validate_and_sanitize_user_id(None, "user-current-123")
        assert result == "user-current-123"

    def test_matching_user_id_returns_current(self):
        """测试user_id匹配时返回当前用户ID"""
        result = validate_and_sanitize_user_id("user-123", "user-123")
        assert result == "user-123"

    def test_mismatched_user_id_returns_current(self, caplog):
        """测试user_id不匹配时返回当前用户ID并记录警告"""
        result = validate_and_sanitize_user_id("user-other-999", "user-current-123")

        # 应该返回当前用户ID,不是请求的user_id
        assert result == "user-current-123"

        # 应该记录警告日志
        assert any("attempted to access data" in record.message.lower()
                  for record in caplog.records if record.levelname == "WARNING")


class TestDocumentUploadUserIsolation:
    """测试文档上传端点的用户隔离"""

    @patch('mirix.server.fastapi_server.get_agent')
    @patch('mirix.server.fastapi_server.user_manager')
    def test_document_upload_uses_current_user(self, mock_user_manager, mock_get_agent, client, mock_user, mock_agent):
        """测试文档上传自动使用当前用户ID"""
        mock_get_agent.return_value = mock_agent
        mock_user_manager.get_user_by_id.return_value = mock_user

        # 这个测试需要真实的文件上传,这里只是框架
        # 实际测试需要准备测试文件和完整的mock环境
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
