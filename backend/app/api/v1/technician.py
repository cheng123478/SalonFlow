"""技师接口：增删改查。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.response import success
from app.schemas.technician import TechnicianCreate, TechnicianOut, TechnicianUpdate
from app.services import technician as service

router = APIRouter(
    prefix="/technician",
    tags=["技师"],
    dependencies=[Depends(get_current_user)],
)


@router.get("")
async def list_technicians(keyword: str | None = None, db: AsyncSession = Depends(get_db)):
    items = await service.list_technicians(db, keyword)
    return success([TechnicianOut.model_validate(i).model_dump() for i in items])


@router.post("")
async def create_technician(body: TechnicianCreate, db: AsyncSession = Depends(get_db)):
    item = await service.create_technician(db, body)
    return success(TechnicianOut.model_validate(item).model_dump(), "创建成功")


@router.get("/{technician_id}")
async def get_technician(technician_id: int, db: AsyncSession = Depends(get_db)):
    item = await service.get_technician(db, technician_id)
    if item is None:
        raise HTTPException(status_code=404, detail="技师不存在")
    return success(TechnicianOut.model_validate(item).model_dump())


@router.put("/{technician_id}")
async def update_technician(technician_id: int, body: TechnicianUpdate, db: AsyncSession = Depends(get_db)):
    item = await service.get_technician(db, technician_id)
    if item is None:
        raise HTTPException(status_code=404, detail="技师不存在")
    item = await service.update_technician(db, item, body)
    return success(TechnicianOut.model_validate(item).model_dump(), "更新成功")


@router.delete("/{technician_id}")
async def delete_technician(technician_id: int, db: AsyncSession = Depends(get_db)):
    item = await service.get_technician(db, technician_id)
    if item is None:
        raise HTTPException(status_code=404, detail="技师不存在")
    await service.delete_technician(db, item)
    return success(message="删除成功")
