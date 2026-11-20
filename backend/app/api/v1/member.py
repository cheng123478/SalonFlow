"""会员接口：增删改查。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.response import success
from app.schemas.member import MemberCreate, MemberOut, MemberUpdate
from app.services import member as service

router = APIRouter(
    prefix="/member",
    tags=["会员"],
    dependencies=[Depends(get_current_user)],
)


@router.get("")
async def list_members(keyword: str | None = None, db: AsyncSession = Depends(get_db)):
    items = await service.list_members(db, keyword)
    return success([MemberOut.model_validate(i).model_dump() for i in items])


@router.post("")
async def create_member(body: MemberCreate, db: AsyncSession = Depends(get_db)):
    item = await service.create_member(db, body)
    return success(MemberOut.model_validate(item).model_dump(), "创建成功")


@router.get("/{member_id}")
async def get_member(member_id: int, db: AsyncSession = Depends(get_db)):
    item = await service.get_member(db, member_id)
    if item is None:
        raise HTTPException(status_code=404, detail="会员不存在")
    return success(MemberOut.model_validate(item).model_dump())


@router.put("/{member_id}")
async def update_member(member_id: int, body: MemberUpdate, db: AsyncSession = Depends(get_db)):
    item = await service.get_member(db, member_id)
    if item is None:
        raise HTTPException(status_code=404, detail="会员不存在")
    item = await service.update_member(db, item, body)
    return success(MemberOut.model_validate(item).model_dump(), "更新成功")


@router.delete("/{member_id}")
async def delete_member(member_id: int, db: AsyncSession = Depends(get_db)):
    item = await service.get_member(db, member_id)
    if item is None:
        raise HTTPException(status_code=404, detail="会员不存在")
    await service.delete_member(db, item)
    return success(message="删除成功")
