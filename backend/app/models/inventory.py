"""库存物料表 + 出入库流水表。"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    threshold: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class InventoryRecord(Base):
    __tablename__ = "inventory_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inventory_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    change_type: Mapped[str] = mapped_column(String(10), nullable=False)  # in / out
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    remark: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
