"""订单表：服务消费记录（会员手机号 + 技师 + 项目 + 金额 + 支付状态）。"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    technician_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    project: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    pay_status: Mapped[str] = mapped_column(String(20), default="unpaid", nullable=False)  # unpaid / paid
    order_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    remark: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
