import uuid
from typing import Optional
from sqlalchemy.orm import Session

from mirix.orm.user_settings import UserSettings
from mirix.orm.errors import NoResultFound
from mirix.schemas.user_settings import (
    UserSettingsCreate,
    UserSettingsUpdate,
    UserSettingsResponse
)
from mirix.utils import enforce_types


class UserSettingsManager:
    """Manager class to handle business logic related to User Settings."""

    def __init__(self):
        from mirix.server.server import db_context
        self.session_maker = db_context

    @enforce_types
    def get_or_create_user_settings(self, user_id: str) -> UserSettingsResponse:
        """
        获取或创建用户设置

        如果用户设置不存在，创建默认设置并返回
        """
        with self.session_maker() as session:
            try:
                # 尝试获取现有设置
                settings = session.query(UserSettings).filter(
                    UserSettings.user_id == user_id,
                    UserSettings.is_deleted == False
                ).first()

                if settings:
                    return UserSettingsResponse.model_validate(settings)
                else:
                    # 创建默认设置，使用 UUID
                    default_settings = UserSettings(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        chat_model="deepseek-chat",
                        memory_model="deepseek-chat",
                        timezone="America/New_York (UTC-5:00)",
                        persona="helpful_assistant",
                        persona_text=None,
                        ui_preferences={},
                        custom_settings={}
                    )
                    session.add(default_settings)
                    session.commit()
                    session.refresh(default_settings)
                    return UserSettingsResponse.model_validate(default_settings)

            except Exception as e:
                session.rollback()
                raise e

    @enforce_types
    def update_user_settings(
        self,
        user_id: str,
        updates: UserSettingsUpdate
    ) -> UserSettingsResponse:
        """
        更新用户设置

        如果设置不存在，先创建然后更新
        """
        with self.session_maker() as session:
            try:
                # 获取或创建设置
                settings = session.query(UserSettings).filter(
                    UserSettings.user_id == user_id,
                    UserSettings.is_deleted == False
                ).first()

                if not settings:
                    # 如果不存在，创建新设置
                    settings = UserSettings(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        chat_model="deepseek-chat",
                        memory_model="deepseek-chat",
                        timezone="America/New_York (UTC-5:00)",
                        persona="helpful_assistant"
                    )
                    session.add(settings)

                # 更新提供的字段
                update_data = updates.model_dump(exclude_unset=True, exclude_none=False)
                for key, value in update_data.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)

                session.commit()
                session.refresh(settings)
                return UserSettingsResponse.model_validate(settings)

            except Exception as e:
                session.rollback()
                raise e

    @enforce_types
    def update_chat_model(self, user_id: str, chat_model: str) -> UserSettingsResponse:
        """更新用户的聊天模型设置"""
        return self.update_user_settings(
            user_id,
            UserSettingsUpdate(chat_model=chat_model)
        )

    @enforce_types
    def update_memory_model(self, user_id: str, memory_model: str) -> UserSettingsResponse:
        """更新用户的记忆模型设置"""
        return self.update_user_settings(
            user_id,
            UserSettingsUpdate(memory_model=memory_model)
        )

    @enforce_types
    def update_timezone(self, user_id: str, timezone: str) -> UserSettingsResponse:
        """更新用户的时区设置"""
        return self.update_user_settings(
            user_id,
            UserSettingsUpdate(timezone=timezone)
        )

    @enforce_types
    def update_persona(
        self,
        user_id: str,
        persona: Optional[str] = None,
        persona_text: Optional[str] = None
    ) -> UserSettingsResponse:
        """更新用户的角色设置"""
        updates = UserSettingsUpdate()
        if persona is not None:
            updates.persona = persona
        if persona_text is not None:
            updates.persona_text = persona_text
        return self.update_user_settings(user_id, updates)

    @enforce_types
    def delete_user_settings(self, user_id: str) -> bool:
        """删除用户设置（通常在删除用户时调用）"""
        with self.session_maker() as session:
            try:
                settings = session.query(UserSettings).filter(
                    UserSettings.user_id == user_id,
                    UserSettings.is_deleted == False
                ).first()

                if settings:
                    # 使用软删除
                    settings.is_deleted = True
                    session.commit()
                    return True
                return False

            except Exception as e:
                session.rollback()
                raise e
