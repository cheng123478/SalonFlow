"""预约接口：增删改查 + 时段冲突校验。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.response import success
from app.schemas.reserve import ReserveCreate, ReserveOut, ReserveUpdate
from app.services import reserve as service

router = APIRouter(
    prefix="/reserve",
    tags=["预约"],
    dependencies=[Depends(get_current_user)],
)


@router.get("")
async def list_reserves(
    technician_id: int | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    items = await service.list_reserves(db, technician_id, status)
    return success([ReserveOut.model_validate(i).model_dump() for i in items])


@router.post("")
async def create_reserve(body: ReserveCreate, db: AsyncSession = Depends(get_db)):
    item = await service.create_reserve(db, body)
    return success(ReserveOut.model_validate(item).model_dump(), "预约成功")


@router.get("/{reserve_id}")
async def get_reserve(reserve_id: int, db: AsyncSession = Depends(get_db)):
    item = await service.get_reserve(db, reserve_id)
    if item is None:
        raise HTTPException(status_code=404, detail="预约不存在")
    return success(ReserveOut.model_validate(item).model_dump())


@router.put("/{reserve_id}")
async def update_reserve(reserve_id: int, body: ReserveUpdate, db: AsyncSession = Depends(get_db)):
    item = await service.get_reserve(db, reserve_id)
    if item is None:
        raise HTTPException(status_code=404, detail="预约不存在")
    item = await service.update_reserve(db, item, body)
    return success(ReserveOut.model_validate(item).model_dump(), "更新成功")


@router.delete("/{reserve_id}")
async def delete_reserve(reserve_id: int, db: AsyncSession = Depends(get_db)):
    item = await service.get_reserve(db, reserve_id)
    if item is None:
        raise HTTPException(status_code=404, detail="预约不存在")
    await service.delete_reserve(db, item)
    return success(message="删除成功")
