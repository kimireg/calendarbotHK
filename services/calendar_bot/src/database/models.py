"""
数据库模型
使用 SQLAlchemy ORM
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class UserState(Base):
    """用户状态表"""
    __tablename__ = "user_state"

    user_id = Column(Integer, primary_key=True)
    current_timezone = Column(String, default="Asia/Singapore", nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserState(user_id={self.user_id}, timezone={self.current_timezone})>"


class EventHistory(Base):
    """事件历史表"""
    __tablename__ = "event_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    calendar_id = Column(String, nullable=False)
    google_event_id = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EventHistory(id={self.id}, summary={self.summary})>"
