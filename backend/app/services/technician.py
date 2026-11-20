"""技师业务逻辑。"""
from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reserve import Reserve
from app.models.technician import Technician
from app.schemas.technician import TechnicianCreate, TechnicianUpdate


async def list_technicians(db: AsyncSession, keyword: str | None = None):
    stmt = select(Technician).order_by(Technician.id.desc())
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Technician.name.like(like), Technician.skills.like(like)))
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_technician(db: AsyncSession, technician_id: int):
    return await db.get(Technician, technician_id)


async def create_technician(db: AsyncSession, data: TechnicianCreate):
    technician = Technician(**data.model_dump())
    db.add(technician)
    await db.commit()
    await db.refresh(technician)
    return technician


async def update_technician(db: AsyncSession, technician: Technician, data: TechnicianUpdate):
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(technician, key, value)
    await db.commit()
    await db.refresh(technician)
    return technician


async def delete_technician(db: AsyncSession, technician: Technician):
    result = await db.execute(
        select(Reserve).where(Reserve.technician_id == technician.id).limit(1)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="该技师存在预约记录，无法删除")
    await db.delete(technician)
    await db.commit()
