"""
数据库访问层
提供数据操作接口
"""
import os
import logging
from typing import Optional, Tuple
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, UserState, EventHistory

logger = logging.getLogger(__name__)


class DatabaseRepository:
    """数据库仓库"""

    def __init__(self, db_path: str):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 创建引擎
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,  # 生产环境不打印 SQL
            connect_args={"check_same_thread": False}  # SQLite 多线程支持
        )

        # 创建表
        Base.metadata.create_all(self.engine)

        # 创建会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info(f"✅ Database initialized: {db_path}")

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    # ==================== 用户状态相关 ====================

    def get_user_timezone(self, user_id: int) -> str:
        """
        获取用户时区

        Args:
            user_id: 用户 ID

        Returns:
            时区字符串
        """
        with self.get_session() as session:
            user_state = session.query(UserState).filter_by(user_id=user_id).first()
            if user_state:
                return user_state.current_timezone
            return "Asia/Singapore"  # 默认时区

    def set_user_timezone(self, user_id: int, timezone: str) -> None:
        """
        设置用户时区

        Args:
            user_id: 用户 ID
            timezone: 时区字符串
        """
        with self.get_session() as session:
            user_state = session.query(UserState).filter_by(user_id=user_id).first()

            if user_state:
                # 更新现有记录
                user_state.current_timezone = timezone
            else:
                # 创建新记录
                user_state = UserState(user_id=user_id, current_timezone=timezone)
                session.add(user_state)

            session.commit()
            logger.info(f"✅ User {user_id} timezone set to {timezone}")

    # ==================== 事件历史相关 ====================

    def save_event_history(
        self,
        user_id: int,
        calendar_id: str,
        google_event_id: str,
        summary: str
    ) -> int:
        """
        保存事件历史

        Args:
            user_id: 用户 ID
            calendar_id: 日历 ID
            google_event_id: Google 事件 ID
            summary: 事件标题

        Returns:
            记录 ID
        """
        with self.get_session() as session:
            event = EventHistory(
                user_id=user_id,
                calendar_id=calendar_id,
                google_event_id=google_event_id,
                summary=summary
            )
            session.add(event)
            session.commit()
            session.refresh(event)

            logger.info(f"✅ Event history saved: {summary} (ID: {event.id})")
            return event.id

    def get_event_from_history(self, event_id: int) -> Optional[Tuple[str, str, str]]:
        """
        从历史中获取事件信息

        Args:
            event_id: 记录 ID

        Returns:
            (calendar_id, google_event_id, summary) 或 None
        """
        with self.get_session() as session:
            event = session.query(EventHistory).filter_by(id=event_id).first()
            if event:
                return (event.calendar_id, event.google_event_id, event.summary)
            return None

    def get_last_event_summary(self, user_id: int) -> Optional[Tuple[str, str]]:
        """
        获取用户最近的事件摘要

        Args:
            user_id: 用户 ID

        Returns:
            (summary, created_at) 或 None
        """
        with self.get_session() as session:
            event = (
                session.query(EventHistory)
                .filter_by(user_id=user_id)
                .order_by(EventHistory.id.desc())
                .first()
            )

            if event:
                return (event.summary, event.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            return None
