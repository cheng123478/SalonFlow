"""订单业务逻辑。"""
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.schemas.order import OrderCreate, OrderUpdate


async def list_orders(
    db: AsyncSession,
    keyword: str | None = None,
    pay_status: str | None = None,
    technician_id: int | None = None,
):
    stmt = select(Order).order_by(Order.order_time.desc())
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Order.phone.like(like), Order.project.like(like)))
    if pay_status:
        stmt = stmt.where(Order.pay_status == pay_status)
    if technician_id:
        stmt = stmt.where(Order.technician_id == technician_id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_order(db: AsyncSession, order_id: int):
    return await db.get(Order, order_id)


async def create_order(db: AsyncSession, data: OrderCreate):
    order = Order(**data.model_dump())
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def update_order(db: AsyncSession, order: Order, data: OrderUpdate):
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(order, key, value)
    await db.commit()
    await db.refresh(order)
    return order


async def delete_order(db: AsyncSession, order: Order):
    await db.delete(order)
    await db.commit()
