from typing import Optional
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from mirix.orm.mixins import UserMixin
from mirix.orm.sqlalchemy_base import SqlalchemyBase
from mirix.schemas.user_settings import UserSettingsResponse as PydanticUserSettings


class UserSettings(SqlalchemyBase, UserMixin):
    """
    用户个性化设置模型

    存储每个用户的个人偏好设置，包括：
    - 聊天模型配置
    - 记忆模型配置
    - 时区设置
    - 角色设定
    - 其他界面偏好

    继承SqlalchemyBase会自动获得：
    - id 主键字段
    - created_at 和 updated_at 时间戳字段
    - is_deleted 软删除字段

    继承UserMixin会自动获得：
    - user_id 外键字段（指向 users 表）
    """
    __tablename__ = "user_settings"
    __pydantic_model__ = PydanticUserSettings

    # 模型设置
    chat_model: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="聊天模型名称"
    )
    memory_model: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="记忆模型名称"
    )

    # 时区设置
    timezone: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="用户时区"
    )

    # 角色设置
    persona: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="角色名称"
    )
    persona_text: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="自定义角色文本"
    )

    # 界面偏好设置（存储为JSON）
    ui_preferences: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=dict, comment="界面偏好设置"
    )

    # 其他设置（扩展字段，存储为JSON）
    custom_settings: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=dict, comment="自定义设置"
    )

    def __repr__(self):
        return f"<UserSettings(id='{self.id}', user_id='{self.user_id}', chat_model='{self.chat_model}')>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "chat_model": self.chat_model,
            "memory_model": self.memory_model,
            "timezone": self.timezone,
            "persona": self.persona,
            "persona_text": self.persona_text,
            "ui_preferences": self.ui_preferences,
            "custom_settings": self.custom_settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
