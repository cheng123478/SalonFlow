"""执行用户已确认的写操作（二次确认后的落库），复用现有 service 的完整校验。"""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory
from app.schemas.member import MemberCreate
from app.schemas.reserve import ReserveCreate
from app.services import inventory, member, reserve


async def execute_action(db: AsyncSession, action: str, params: dict):
    """根据 action 执行对应写操作。params 为用户确认的 pending_action 参数。"""
    if action == "create_reserve":
        data = ReserveCreate(**params)
        return await reserve.create_reserve(db, data)
    if action == "create_member":
        data = MemberCreate(**params)
        return await member.create_member(db, data)
    if action == "change_stock":
        item = await db.get(Inventory, params.get("inventory_id"))
        if item is None:
            raise HTTPException(status_code=404, detail="物料不存在")
        return await inventory.change_stock(
            db,
            item,
            params["change_type"],
            params["quantity"],
            params.get("remark", ""),
        )
    raise HTTPException(status_code=400, detail=f"未知的写操作：{action}")
