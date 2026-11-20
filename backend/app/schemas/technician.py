"""技师相关 Pydantic 模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TechnicianCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    skills: str = Field(default="", max_length=255)
    rest_days: str = Field(default="", max_length=100)
    schedule_config: str = Field(default="", max_length=500)
    avatar: str = Field(default="", max_length=255)
    is_on_duty: bool = True


class TechnicianUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    skills: str | None = Field(default=None, max_length=255)
    rest_days: str | None = Field(default=None, max_length=100)
    schedule_config: str | None = Field(default=None, max_length=500)
    avatar: str | None = Field(default=None, max_length=255)
    is_on_duty: bool | None = None


class TechnicianOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    skills: str
    rest_days: str
    schedule_config: str
    avatar: str
    is_on_duty: bool
    created_at: datetime
