"""订单相关 Pydantic 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    phone: str = Field(default="", max_length=20)
    technician_id: int = Field(gt=0)
    project: str = Field(default="", max_length=100)
    amount: float = Field(default=0.0, ge=0)
    pay_status: Literal["unpaid", "paid"] = "unpaid"
    order_time: datetime
    remark: str = Field(default="", max_length=255)


class OrderUpdate(BaseModel):
    phone: str | None = Field(default=None, max_length=20)
    technician_id: int | None = Field(default=None, gt=0)
    project: str | None = Field(default=None, max_length=100)
    amount: float | None = Field(default=None, ge=0)
    pay_status: Literal["unpaid", "paid"] | None = None
    order_time: datetime | None = None
    remark: str | None = Field(default=None, max_length=255)


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: str
    technician_id: int
    project: str
    amount: float
    pay_status: str
    order_time: datetime
    remark: str
    created_at: datetime
