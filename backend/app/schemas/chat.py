"""会话与对话历史相关 Pydantic 模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime