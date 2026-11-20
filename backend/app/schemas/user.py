"""用户相关 Pydantic 模型。"""
from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    real_name: str
    user_type: str
    phone: str
