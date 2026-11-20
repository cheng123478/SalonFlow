"""认证相关 Pydantic 模型。"""
from pydantic import BaseModel

from app.schemas.user import UserOut


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    real_name: str = ""
    phone: str = ""


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
