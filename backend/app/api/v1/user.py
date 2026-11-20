"""用户接口：当前登录用户信息。"""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.response import success
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/user", tags=["用户"])


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return success(UserOut.model_validate(current_user).model_dump())
