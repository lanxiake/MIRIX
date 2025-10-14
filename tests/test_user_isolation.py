"""
用户数据隔离单元测试

测试ORM层和API层的用户数据隔离机制,确保用户只能访问自己的数据
"""

import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy import select

from mirix.orm.sqlalchemy_base import SqlalchemyBase, AccessType
from mirix.schemas.user import User as PydanticUser
from mirix.server.fastapi_server import validate_and_sanitize_user_id


class TestApplyAccessPredicate:
    """测试ORM层的访问控制谓词"""
    
    def test_user_level_access_control_success(self):
        """测试USER级别访问控制正常情况"""
        # 使用真实的EpisodicEvent模型来测试
        from mirix.orm.episodic_memory import EpisodicEvent

        # 创建mock actor
        actor = Mock()
        actor.id = "user-123"
        actor.organization_id = "org-456"

        # 创建mock query
        query = Mock()
        query.where = Mock(return_value=query)

        # 调用apply_access_predicate on EpisodicEvent class
        result = EpisodicEvent.apply_access_predicate(
            query=query,
            actor=actor,
            access=["read"],
            access_type=AccessType.USER
        )

        # 验证where被调用 (user_id and is_deleted filters are applied)
        assert query.where.called
        assert result == query
        
    def test_user_level_access_control_actor_none(self):
        """测试USER级别访问控制 - actor为None时抛出错误"""
        query = Mock()
        
        # 调用时actor=None应该抛出ValueError
        with pytest.raises(ValueError) as exc_info:
            SqlalchemyBase.apply_access_predicate(
                query=query,
                actor=None,
                access=["read"],
                access_type=AccessType.USER
            )
        
        assert "actor parameter is required" in str(exc_info.value)
    
    def test_user_level_access_control_no_user_id(self):
        """测试USER级别访问控制 - actor无id属性时抛出错误"""
        # 创建没有id属性的mock actor
        actor = Mock(spec=[])  # 空spec意味着没有任何属性
        actor.organization_id = "org-456"
        
        query = Mock()
        
        # 调用时actor无id属性应该抛出ValueError
        with pytest.raises((ValueError, AttributeError)) as exc_info:
            SqlalchemyBase.apply_access_predicate(
                query=query,
                actor=actor,
                access=["read"],
                access_type=AccessType.USER
            )
        
        # 错误信息应该提示缺少user accessor
        assert "user accessor" in str(exc_info.value) or "id" in str(exc_info.value)


class TestValidateAndSanitizeUserId:
    """测试user_id参数验证函数"""
    
    def test_user_id_none_returns_current(self):
        """测试user_id为None时返回当前用户ID"""
        result = validate_and_sanitize_user_id(None, "user-current")
        assert result == "user-current"
    
    def test_user_id_matches_current(self):
        """测试user_id匹配当前用户ID"""
        result = validate_and_sanitize_user_id("user-123", "user-123")
        assert result == "user-123"
    
    def test_user_id_not_matches_current(self, caplog):
        """测试user_id不匹配当前用户ID时返回当前用户ID并记录警告"""
        result = validate_and_sanitize_user_id("user-other", "user-current")
        
        # 应该返回当前用户ID
        assert result == "user-current"
        
        # 应该记录警告日志
        assert any("attempted to access data of user" in record.message 
                  for record in caplog.records)


class TestUserIsolationIntegration:
    """集成测试 - 测试完整的用户隔离流程"""
    
    @pytest.mark.skip(reason="需要数据库环境,在集成测试中运行")
    def test_episodic_memory_user_isolation(self):
        """测试情景记忆的用户隔离"""
        # 此测试需要真实数据库环境
        # 将在integration测试中实现
        pass
    
    @pytest.mark.skip(reason="需要数据库环境,在集成测试中运行")  
    def test_semantic_memory_user_isolation(self):
        """测试语义记忆的用户隔离"""
        pass
    
    @pytest.mark.skip(reason="需要数据库环境,在集成测试中运行")
    def test_agent_user_isolation(self):
        """测试智能体的用户隔离"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

