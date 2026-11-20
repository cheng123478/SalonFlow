"""库存相关 Pydantic 模型。"""
from datetime import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class InventoryCreate(BaseModel):
    name: str = Field(max_length=100)
    quantity: int = Field(default=0, ge=0)
    threshold: int = Field(default=10, ge=0)
    unit: str = Field(default="", max_length=20)


class InventoryUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    quantity: int | None = Field(default=None, ge=0)
    threshold: int | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=20)


class InventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    quantity: int
    threshold: int
    unit: str
    created_at: datetime

    @computed_field
    @property
    def low_stock(self) -> bool:
        """库存是否低于安全阈值。"""
        return self.quantity < self.threshold


class StockChangeIn(BaseModel):
    change_type: Literal["in", "out"]
    quantity: int = Field(gt=0)
    remark: str = Field(default="", max_length=255)


class InventoryRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inventory_id: int
    change_type: str
    quantity: int
    remark: str
    created_at: datetime
