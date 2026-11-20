"""认证接口：登录与注册。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import success
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["认证"])


def _token_response(user: User, message: str) -> dict:
    token = create_access_token(user.id, user.user_type)
    data = LoginResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )
    return success(data.model_dump(), message=message)


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    return _token_response(user, "登录成功")


@router.post("/register")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 公开注册一律落为顾客角色；店长/店员由管理员在后台创建，避免越权提权。
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        real_name=body.real_name,
        user_type="customer",
        phone=body.phone,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return _token_response(user, "注册成功")
