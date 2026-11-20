"""双层记忆持久化：会话表（session）+ 对话历史表（chat_history）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ChatSession(Base):
    """会话表：一次连续对话的边界，按 user_id 隔离。"""

    __tablename__ = "chat_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_key: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), default="新对话", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ChatMessage(Base):
    """对话历史表：会话内的逐条消息，双层记忆的第二层。"""

    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_session.id"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user / assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())