"""技师表：姓名、擅长项目、休息日、排班配置。"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Technician(Base):
    __tablename__ = "technician"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    skills: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    rest_days: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    schedule_config: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    is_on_duty: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
