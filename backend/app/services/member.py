"""会员业务逻辑。"""
from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member
from app.schemas.member import MemberCreate, MemberUpdate


async def list_members(db: AsyncSession, keyword: str | None = None):
    stmt = select(Member).order_by(Member.id.desc())
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Member.name.like(like), Member.phone.like(like)))
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_member(db: AsyncSession, member_id: int):
    return await db.get(Member, member_id)


async def _phone_exists(db: AsyncSession, phone: str, exclude_id: int | None = None) -> bool:
    stmt = select(Member).where(Member.phone == phone)
    if exclude_id is not None:
        stmt = stmt.where(Member.id != exclude_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def create_member(db: AsyncSession, data: MemberCreate):
    if await _phone_exists(db, data.phone):
        raise HTTPException(status_code=400, detail="手机号已存在")
    member = Member(**data.model_dump())
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


async def update_member(db: AsyncSession, member: Member, data: MemberUpdate):
    payload = data.model_dump(exclude_unset=True)
    phone = payload.get("phone")
    if phone is not None and await _phone_exists(db, phone, exclude_id=member.id):
        raise HTTPException(status_code=400, detail="手机号已存在")
    for key, value in payload.items():
        setattr(member, key, value)
    await db.commit()
    await db.refresh(member)
    return member


async def delete_member(db: AsyncSession, member: Member):
    await db.delete(member)
    await db.commit()
