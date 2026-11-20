"""库存接口：增删改查 + 出入库 + 低库存预警。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.response import success
from app.schemas.inventory import (
    InventoryCreate,
    InventoryOut,
    InventoryRecordOut,
    InventoryUpdate,
    StockChangeIn,
)
from app.services import inventory as service

router = APIRouter(
    prefix="/inventory",
    tags=["库存"],
    dependencies=[Depends(get_current_user)],
)


@router.get("")
async def list_inventory(keyword: str | None = None, db: AsyncSession = Depends(get_db)):
    items = await service.list_inventory(db, keyword)
    return success([InventoryOut.model_validate(i).model_dump() for i in items])


@router.get("/warnings")
async def list_warnings(db: AsyncSession = Depends(get_db)):
    items = await service.list_warnings(db)
    return success([InventoryOut.model_validate(i).model_dump() for i in items])


@router.get("/records")
async def list_records(inventory_id: int | None = None, db: AsyncSession = Depends(get_db)):
    records = await service.list_records(db, inventory_id)
    return success([InventoryRecordOut.model_validate(r).model_dump() for r in records])


@router.post("")
async def create_inventory(body: InventoryCreate, db: AsyncSession = Depends(get_db)):
    item = await service.create_inventory(db, body)
    return success(InventoryOut.model_validate(item).model_dump(), "创建成功")


@router.get("/{inventory_id}")
async def get_inventory(inventory_id: int, db: AsyncSession = Depends(get_db)):
    item = await service.get_inventory(db, inventory_id)
    if item is None:
        raise HTTPException(status_code=404, detail="物料不存在")
    return success(InventoryOut.model_validate(item).model_dump())


@router.put("/{inventory_id}")
async def update_inventory(inventory_id: int, body: InventoryUpdate, db: AsyncSession = Depends(get_db)):
    item = await service.get_inventory(db, inventory_id)
    if item is None:
        raise HTTPException(status_code=404, detail="物料不存在")
    item = await service.update_inventory(db, item, body)
    return success(InventoryOut.model_validate(item).model_dump(), "更新成功")


@router.delete("/{inventory_id}")
async def delete_inventory(inventory_id: int, db: AsyncSession = Depends(get_db)):
    item = await service.get_inventory(db, inventory_id)
    if item is None:
        raise HTTPException(status_code=404, detail="物料不存在")
    await service.delete_inventory(db, item)
    return success(message="删除成功")


@router.post("/{inventory_id}/stock")
async def change_stock(inventory_id: int, body: StockChangeIn, db: AsyncSession = Depends(get_db)):
    item = await service.get_inventory(db, inventory_id)
    if item is None:
        raise HTTPException(status_code=404, detail="物料不存在")
    item = await service.change_stock(db, item, body.change_type, body.quantity, body.remark)
    return success(InventoryOut.model_validate(item).model_dump(), "出入库成功")
