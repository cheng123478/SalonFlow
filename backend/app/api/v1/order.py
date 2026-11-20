"""订单接口：增删改查。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.response import success
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate
from app.services import order as service

router = APIRouter(
    prefix="/order",
    tags=["订单"],
    dependencies=[Depends(get_current_user)],
)


@router.get("")
async def list_orders(
    keyword: str | None = None,
    pay_status: str | None = None,
    technician_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    items = await service.list_orders(db, keyword, pay_status, technician_id)
    return success([OrderOut.model_validate(i).model_dump() for i in items])


@router.post("")
async def create_order(body: OrderCreate, db: AsyncSession = Depends(get_db)):
    item = await service.create_order(db, body)
    return success(OrderOut.model_validate(item).model_dump(), "创建成功")


@router.get("/{order_id}")
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    item = await service.get_order(db, order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    return success(OrderOut.model_validate(item).model_dump())


@router.put("/{order_id}")
async def update_order(order_id: int, body: OrderUpdate, db: AsyncSession = Depends(get_db)):
    item = await service.get_order(db, order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    item = await service.update_order(db, item, body)
    return success(OrderOut.model_validate(item).model_dump(), "更新成功")


@router.delete("/{order_id}")
async def delete_order(order_id: int, db: AsyncSession = Depends(get_db)):
    item = await service.get_order(db, order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    await service.delete_order(db, item)
    return success(message="删除成功")
