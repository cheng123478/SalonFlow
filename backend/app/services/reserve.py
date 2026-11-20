"""预约业务逻辑：含时段冲突校验。"""
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reserve import Reserve
from app.models.technician import Technician
from app.schemas.reserve import ReserveCreate, ReserveUpdate

# 冲突窗口：同一技师前后 1 小时内视为冲突
CONFLICT_WINDOW = timedelta(hours=1)


async def _has_conflict(
    db: AsyncSession,
    technician_id: int,
    reserve_time,
    exclude_id: int | None = None,
) -> bool:
    start = reserve_time - CONFLICT_WINDOW
    end = reserve_time + CONFLICT_WINDOW
    stmt = select(Reserve).where(
        Reserve.technician_id == technician_id,
        Reserve.reserve_time >= start,
        Reserve.reserve_time <= end,
        Reserve.status.in_(["pending", "confirmed"]),
    )
    if exclude_id is not None:
        stmt = stmt.where(Reserve.id != exclude_id)
    result = await db.execute(stmt)
    return result.scalars().first() is not None


async def list_reserves(
    db: AsyncSession,
    technician_id: int | None = None,
    status: str | None = None,
):
    stmt = select(Reserve).order_by(Reserve.reserve_time.desc())
    if technician_id:
        stmt = stmt.where(Reserve.technician_id == technician_id)
    if status:
        stmt = stmt.where(Reserve.status == status)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_reserve(db: AsyncSession, reserve_id: int):
    return await db.get(Reserve, reserve_id)


async def create_reserve(db: AsyncSession, data: ReserveCreate):
    if await db.get(Technician, data.technician_id) is None:
        raise HTTPException(status_code=400, detail="技师不存在")
    if await _has_conflict(db, data.technician_id, data.reserve_time):
        raise HTTPException(status_code=400, detail="该技师在此时段已有预约，请选择其他时间")
    reserve = Reserve(**data.model_dump())
    db.add(reserve)
    await db.commit()
    await db.refresh(reserve)
    return reserve


async def update_reserve(db: AsyncSession, reserve: Reserve, data: ReserveUpdate):
    payload = data.model_dump(exclude_unset=True)
    technician_id = payload.get("technician_id", reserve.technician_id)
    reserve_time = payload.get("reserve_time", reserve.reserve_time)

    if technician_id is None or reserve_time is None:
        raise HTTPException(status_code=400, detail="technician_id 和 reserve_time 不能为空")
    if await db.get(Technician, technician_id) is None:
        raise HTTPException(status_code=400, detail="技师不存在")
    if await _has_conflict(db, technician_id, reserve_time, exclude_id=reserve.id):
        raise HTTPException(status_code=400, detail="该技师在此时段已有预约，请选择其他时间")
    for key, value in payload.items():
        setattr(reserve, key, value)
    await db.commit()
    await db.refresh(reserve)
    return reserve


async def delete_reserve(db: AsyncSession, reserve: Reserve):
    await db.delete(reserve)
    await db.commit()
