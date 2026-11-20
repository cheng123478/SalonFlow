"""会员相关 Pydantic 模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MemberCreate(BaseModel):
    phone: str = Field(min_length=1, max_length=20)
    name: str = Field(default="", max_length=50)
    remark: str = Field(default="", max_length=255)
    balance: float = Field(default=0.0, ge=0)
    tags: str = Field(default="", max_length=255)
    hair_remark: str = Field(default="", max_length=255)
    last_dye_time: datetime | None = None


class MemberUpdate(BaseModel):
    phone: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, max_length=50)
    remark: str | None = Field(default=None, max_length=255)
    balance: float | None = Field(default=None, ge=0)
    tags: str | None = Field(default=None, max_length=255)
    hair_remark: str | None = Field(default=None, max_length=255)
    last_dye_time: datetime | None = None


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: str
    name: str
    remark: str
    balance: float
    tags: str
    hair_remark: str
    last_dye_time: datetime | None
    created_at: datetime
