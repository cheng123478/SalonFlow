"""会员表：手机号、姓名、储值余额、标签、发质备注、烫染记录。"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Member(Base):
    __tablename__ = "member"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    remark: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    tags: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    hair_remark: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    last_dye_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
