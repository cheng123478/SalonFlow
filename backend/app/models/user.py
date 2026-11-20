"""用户表：店长(owner) / 店员(staff) / 顾客(customer)。"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    real_name: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    user_type: Mapped[str] = mapped_column(String(20), default="staff", nullable=False)
    phone: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
