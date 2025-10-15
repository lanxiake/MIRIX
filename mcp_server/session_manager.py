"""
MCP Server 会话管理器

管理多用户和多会话的上下文隔离，确保每个连接都有独立的用户上下文。

主要功能：
- 会话创建和销毁
- 用户ID与会话绑定
- 会话上下文管理
- 并发会话支持

设计原则：
- 线程安全的会话管理
- 支持同一用户多个会话
- 支持多用户并发访问
- 会话自动清理机制
"""

import asyncio
import logging
import uuid
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# 当前会话上下文变量
current_session_id: ContextVar[Optional[str]] = ContextVar("current_session_id", default=None)
current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)


@dataclass
class Session:
    """会话信息"""
    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    request_count: int = 0

    def update_activity(self):
        """更新会话活动时间"""
        self.last_active = datetime.now()
        self.request_count += 1


class SessionManager:
    """
    会话管理器

    负责管理所有活跃的用户会话，提供会话创建、查询、更新和清理功能。
    支持同一用户创建多个独立会话（例如多个浏览器窗口）。
    """

    def __init__(self, session_timeout: int = 3600):
        """
        初始化会话管理器

        Args:
            session_timeout: 会话超时时间（秒），默认1小时
        """
        self._sessions: Dict[str, Session] = {}  # session_id -> Session
        self._user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self._lock = asyncio.Lock()
        self._session_timeout = timedelta(seconds=session_timeout)
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"会话管理器已初始化，超时时间: {session_timeout}秒")

    async def start_cleanup_task(self):
        """启动会话清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("会话清理任务已启动")

    async def stop_cleanup_task(self):
        """停止会话清理任务"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("会话清理任务已停止")

    async def _cleanup_loop(self):
        """定期清理过期会话"""
        try:
            while True:
                await asyncio.sleep(300)  # 每5分钟清理一次
                await self.cleanup_expired_sessions()
        except asyncio.CancelledError:
            logger.info("会话清理循环已取消")

    async def create_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        """
        创建新会话或获取已存在的会话

        Args:
            user_id: 用户ID
            session_id: 可选的会话ID，如果不提供则自动生成

        Returns:
            str: 会话ID
        """
        async with self._lock:
            # 生成会话ID
            if session_id is None:
                session_id = str(uuid.uuid4())

            # 检查会话是否已存在
            if session_id in self._sessions:
                existing_session = self._sessions[session_id]
                # 更新活动时间
                existing_session.update_activity()
                logger.debug(f"会话已存在，更新活动时间: session_id={session_id}, user_id={user_id}")
                return session_id

            # 创建新会话对象
            session = Session(
                session_id=session_id,
                user_id=user_id
            )

            # 保存会话
            self._sessions[session_id] = session

            # 添加到用户会话集合
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = set()
            self._user_sessions[user_id].add(session_id)

            logger.info(f"创建新会话: session_id={session_id}, user_id={user_id}")
            logger.info(f"用户 {user_id} 当前活跃会话数: {len(self._user_sessions[user_id])}")

            return session_id

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            Optional[Session]: 会话对象，如果不存在则返回None
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.update_activity()
            return session

    async def get_user_id(self, session_id: str) -> Optional[str]:
        """
        根据会话ID获取用户ID

        Args:
            session_id: 会话ID

        Returns:
            Optional[str]: 用户ID，如果会话不存在则返回None
        """
        session = await self.get_session(session_id)
        return session.user_id if session else None

    async def get_user_sessions(self, user_id: str) -> Set[str]:
        """
        获取用户的所有活跃会话

        Args:
            user_id: 用户ID

        Returns:
            Set[str]: 会话ID集合
        """
        async with self._lock:
            return self._user_sessions.get(user_id, set()).copy()

    async def remove_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功删除
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False

            # 从会话字典中删除
            del self._sessions[session_id]

            # 从用户会话集合中删除
            user_id = session.user_id
            if user_id in self._user_sessions:
                self._user_sessions[user_id].discard(session_id)
                # 如果用户没有活跃会话了，删除用户记录
                if not self._user_sessions[user_id]:
                    del self._user_sessions[user_id]

            logger.info(f"删除会话: session_id={session_id}, user_id={user_id}")

            return True

    async def cleanup_expired_sessions(self) -> int:
        """
        清理过期的会话

        Returns:
            int: 清理的会话数量
        """
        async with self._lock:
            now = datetime.now()
            expired_sessions = []

            for session_id, session in self._sessions.items():
                if now - session.last_active > self._session_timeout:
                    expired_sessions.append(session_id)

            # 删除过期会话
            for session_id in expired_sessions:
                session = self._sessions[session_id]
                del self._sessions[session_id]

                # 从用户会话集合中删除
                user_id = session.user_id
                if user_id in self._user_sessions:
                    self._user_sessions[user_id].discard(session_id)
                    if not self._user_sessions[user_id]:
                        del self._user_sessions[user_id]

            if expired_sessions:
                logger.info(f"清理了 {len(expired_sessions)} 个过期会话")

            return len(expired_sessions)

    async def get_stats(self) -> Dict[str, any]:
        """
        获取会话统计信息

        Returns:
            Dict[str, any]: 统计信息
        """
        async with self._lock:
            total_sessions = len(self._sessions)
            total_users = len(self._user_sessions)

            # 计算每个用户的会话数
            user_session_counts = {
                user_id: len(sessions)
                for user_id, sessions in self._user_sessions.items()
            }

            # 计算平均会话数
            avg_sessions_per_user = (
                sum(user_session_counts.values()) / len(user_session_counts)
                if user_session_counts else 0
            )

            return {
                "total_sessions": total_sessions,
                "total_users": total_users,
                "avg_sessions_per_user": avg_sessions_per_user,
                "user_session_counts": user_session_counts
            }

    def set_session_context(self, session_id: str, user_id: str):
        """
        设置当前线程/协程的会话上下文

        Args:
            session_id: 会话ID
            user_id: 用户ID
        """
        current_session_id.set(session_id)
        current_user_id.set(user_id)
        logger.debug(f"设置会话上下文: session_id={session_id}, user_id={user_id}")

    def clear_session_context(self):
        """清除当前线程/协程的会话上下文"""
        current_session_id.set(None)
        current_user_id.set(None)
        logger.debug("清除会话上下文")

    @staticmethod
    def get_current_session_id() -> Optional[str]:
        """获取当前会话ID"""
        return current_session_id.get()

    @staticmethod
    def get_current_user_id() -> Optional[str]:
        """获取当前用户ID"""
        return current_user_id.get()


# 全局会话管理器实例
_global_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    获取全局会话管理器实例

    Returns:
        SessionManager: 会话管理器实例
    """
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager


def set_session_manager(manager: SessionManager):
    """
    设置全局会话管理器实例

    Args:
        manager: 会话管理器实例
    """
    global _global_session_manager
    _global_session_manager = manager
