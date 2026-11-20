"""库存业务逻辑：出入库、流水、低库存预警。"""
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory, InventoryRecord
from app.schemas.inventory import InventoryCreate, InventoryUpdate


async def list_inventory(db: AsyncSession, keyword: str | None = None):
    stmt = select(Inventory).order_by(Inventory.id.desc())
    if keyword:
        stmt = stmt.where(Inventory.name.like(f"%{keyword}%"))
    result = await db.execute(stmt)
    return result.scalars().all()


async def list_warnings(db: AsyncSession):
    stmt = select(Inventory).where(Inventory.quantity < Inventory.threshold).order_by(Inventory.id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_inventory(db: AsyncSession, inventory_id: int):
    return await db.get(Inventory, inventory_id)


async def create_inventory(db: AsyncSession, data: InventoryCreate):
    item = Inventory(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_inventory(db: AsyncSession, item: Inventory, data: InventoryUpdate):
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_inventory(db: AsyncSession, item: Inventory):
    # 删除物料时一并删除其出入库流水，避免留下孤儿记录
    await db.execute(delete(InventoryRecord).where(InventoryRecord.inventory_id == item.id))
    await db.delete(item)
    await db.commit()


async def change_stock(
    db: AsyncSession,
    item: Inventory,
    change_type: str,
    quantity: int,
    remark: str = "",
):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="数量必须为正数")
    if change_type == "out":
        if item.quantity < quantity:
            raise HTTPException(status_code=400, detail=f"库存不足，当前仅 {item.quantity}{item.unit}")
        item.quantity -= quantity
    elif change_type == "in":
        item.quantity += quantity
    else:
        raise HTTPException(status_code=400, detail="change_type 必须为 in 或 out")

    record = InventoryRecord(
        inventory_id=item.id,
        change_type=change_type,
        quantity=quantity,
        remark=remark,
    )
    db.add(record)
    await db.commit()
    await db.refresh(item)
    return item


async def list_records(db: AsyncSession, inventory_id: int | None = None):
    stmt = select(InventoryRecord).order_by(InventoryRecord.id.desc())
    if inventory_id:
        stmt = stmt.where(InventoryRecord.inventory_id == inventory_id)
    result = await db.execute(stmt)
    return result.scalars().all()
