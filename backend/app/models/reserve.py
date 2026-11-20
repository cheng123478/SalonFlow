"""预约表：技师、顾客手机号、预约时间、项目、状态。"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Reserve(Base):
    __tablename__ = "reserve"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    technician_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    reserve_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    project: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
