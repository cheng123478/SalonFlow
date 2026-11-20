"""预约相关 Pydantic 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReserveCreate(BaseModel):
    technician_id: int = Field(gt=0)
    phone: str = Field(min_length=1, max_length=20)
    reserve_time: datetime
    project: str = Field(default="", max_length=100)
    status: Literal["pending", "confirmed", "completed", "cancelled"] = "pending"


class ReserveUpdate(BaseModel):
    technician_id: int | None = Field(default=None, gt=0)
    phone: str | None = Field(default=None, min_length=1, max_length=20)
    reserve_time: datetime | None = None
    project: str | None = Field(default=None, max_length=100)
    status: Literal["pending", "confirmed", "completed", "cancelled"] | None = None


class ReserveOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    technician_id: int
    phone: str
    reserve_time: datetime
    project: str
    status: str
    created_at: datetime
