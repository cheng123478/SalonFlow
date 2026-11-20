"""报表聚合统计：工作台汇总卡片、预约分布、Excel 导出数据。"""
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory
from app.models.member import Member
from app.models.order import Order
from app.models.reserve import Reserve
from app.models.technician import Technician

# 预约状态中文标签（导出/展示共用）
RESERVE_STATUS_LABELS = {
    "pending": "待确认",
    "confirmed": "已确认",
    "completed": "已完成",
    "cancelled": "已取消",
}


def _fmt(value) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


async def overview(db: AsyncSession) -> dict:
    """工作台汇总卡片数据。"""
    member_count = await db.scalar(select(func.count(Member.id)))
    balance_total = await db.scalar(select(func.sum(Member.balance)))
    reserve_count = await db.scalar(select(func.count(Reserve.id)))
    reserve_pending = await db.scalar(
        select(func.count(Reserve.id)).where(Reserve.status == "pending")
    )
    low_stock_count = await db.scalar(
        select(func.count(Inventory.id)).where(Inventory.quantity < Inventory.threshold)
    )
    technician_on_duty = await db.scalar(
        select(func.count(Technician.id)).where(Technician.is_on_duty.is_(True))
    )

    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    member_this_month = await db.scalar(
        select(func.count(Member.id)).where(Member.created_at >= month_start)
    )

    return {
        "member_count": member_count or 0,
        "balance_total": float(balance_total) if balance_total is not None else 0.0,
        "member_this_month": member_this_month or 0,
        "reserve_count": reserve_count or 0,
        "reserve_pending": reserve_pending or 0,
        "low_stock_count": low_stock_count or 0,
        "technician_on_duty": technician_on_duty or 0,
    }


async def reserve_status_stats(db: AsyncSession) -> list[dict]:
    rows = (
        await db.execute(
            select(Reserve.status, func.count(Reserve.id)).group_by(Reserve.status)
        )
    ).all()
    return [{"status": status, "count": count} for status, count in rows]


async def reserve_technician_stats(db: AsyncSession) -> list[dict]:
    rows = (
        await db.execute(
            select(Technician.name, func.count(Reserve.id))
            .join(Reserve, Reserve.technician_id == Technician.id)
            .group_by(Technician.name)
            .order_by(func.count(Reserve.id).desc())
        )
    ).all()
    return [{"technician": name, "count": count} for name, count in rows]


async def member_monthly_stats(db: AsyncSession, months: int = 6) -> list[dict]:
    """近 N 月新增会员按月计数（含补零的连续月份）。"""
    now = datetime.now()
    start_year, start_month = now.year, now.month - (months - 1)
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    start = datetime(start_year, start_month, 1)

    created_ats = (
        await db.execute(
            select(Member.created_at).where(Member.created_at >= start)
        )
    ).scalars().all()

    # 生成连续月份标签，保证缺月也返回 0
    labels, y, m = [], start_year, start_month
    for _ in range(months):
        labels.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1

    buckets = {label: 0 for label in labels}
    for created_at in created_ats:
        if created_at is None:
            continue
        label = f"{created_at.year:04d}-{created_at.month:02d}"
        if label in buckets:
            buckets[label] += 1
    return [{"month": label, "count": buckets[label]} for label in labels]


async def export_members(db: AsyncSession) -> tuple[list[str], list[list]]:
    members = (await db.execute(select(Member).order_by(Member.id.desc()))).scalars().all()
    headers = ["姓名", "手机号", "储值余额", "发质备注", "备注", "上次烫染", "创建时间"]
    rows = [
        [
            m.name,
            m.phone,
            float(m.balance),
            m.hair_remark,
            m.remark,
            m.last_dye_time.strftime("%Y-%m-%d") if m.last_dye_time else "",
            _fmt(m.created_at),
        ]
        for m in members
    ]
    return headers, rows


async def export_reserves(db: AsyncSession) -> tuple[list[str], list[list]]:
    rows = (
        await db.execute(
            select(Reserve, Technician.name)
            .join(Technician, Reserve.technician_id == Technician.id)
            .order_by(Reserve.reserve_time.desc())
        )
    ).all()
    headers = ["技师", "手机号", "预约时间", "项目", "状态", "创建时间"]
    data = [
        [
            technician_name,
            reserve.phone,
            reserve.reserve_time.strftime("%Y-%m-%d %H:%M:%S") if reserve.reserve_time else "",
            reserve.project,
            RESERVE_STATUS_LABELS.get(reserve.status, reserve.status),
            _fmt(reserve.created_at),
        ]
        for reserve, technician_name in rows
    ]
    return headers, data


async def export_inventory(db: AsyncSession) -> tuple[list[str], list[list]]:
    items = (await db.execute(select(Inventory).order_by(Inventory.id.desc()))).scalars().all()
    headers = ["物料名称", "库存数量", "安全阈值", "单位", "状态", "创建时间"]
    data = [
        [
            item.name,
            item.quantity,
            item.threshold,
            item.unit,
            "库存不足" if item.quantity < item.threshold else "正常",
            _fmt(item.created_at),
        ]
        for item in items
    ]
    return headers, data


async def revenue_summary(db: AsyncSession) -> dict:
    """营收汇总：总营收、未支付应收、订单总数、本月营收。"""
    total_paid = await db.scalar(
        select(func.sum(Order.amount)).where(Order.pay_status == "paid")
    )
    total_unpaid = await db.scalar(
        select(func.sum(Order.amount)).where(Order.pay_status == "unpaid")
    )
    order_count = await db.scalar(select(func.count(Order.id)))

    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    month_paid = await db.scalar(
        select(func.sum(Order.amount)).where(
            Order.pay_status == "paid", Order.order_time >= month_start
        )
    )

    return {
        "total_paid": float(total_paid) if total_paid is not None else 0.0,
        "total_unpaid": float(total_unpaid) if total_unpaid is not None else 0.0,
        "order_count": order_count or 0,
        "month_paid": float(month_paid) if month_paid is not None else 0.0,
    }


async def revenue_daily_stats(db: AsyncSession, days: int = 30) -> list[dict]:
    """近 N 天已支付营收按日聚合（含补零连续日期）。"""
    start_day = datetime.now().date() - timedelta(days=days - 1)
    start = datetime(start_day.year, start_day.month, start_day.day)

    rows = (
        await db.execute(
            select(Order.order_time, Order.amount).where(
                Order.pay_status == "paid", Order.order_time >= start
            )
        )
    ).all()

    labels, buckets = [], {}
    for i in range(days):
        label = (start_day + timedelta(days=i)).strftime("%Y-%m-%d")
        labels.append(label)
        buckets[label] = 0.0

    for order_time, amount in rows:
        if order_time is None:
            continue
        label = order_time.strftime("%Y-%m-%d")
        if label in buckets:
            buckets[label] += float(amount or 0)

    return [{"date": label, "amount": round(buckets[label], 2)} for label in labels]


async def revenue_technician_stats(db: AsyncSession) -> list[dict]:
    """已支付营收按技师聚合（降序）。"""
    rows = (
        await db.execute(
            select(Technician.name, func.sum(Order.amount))
            .join(Order, Order.technician_id == Technician.id)
            .where(Order.pay_status == "paid")
            .group_by(Technician.name)
            .order_by(func.sum(Order.amount).desc())
        )
    ).all()
    return [{"technician": name, "amount": round(float(total or 0), 2)} for name, total in rows]


async def export_orders(db: AsyncSession) -> tuple[list[str], list[list]]:
    rows = (
        await db.execute(
            select(Order, Technician.name)
            .join(Technician, Order.technician_id == Technician.id)
            .order_by(Order.order_time.desc())
        )
    ).all()
    headers = ["手机号", "技师", "项目", "金额", "支付状态", "服务时间", "备注", "创建时间"]
    data = [
        [
            order.phone,
            technician_name,
            order.project,
            float(order.amount),
            "已支付" if order.pay_status == "paid" else "未支付",
            order.order_time.strftime("%Y-%m-%d %H:%M:%S") if order.order_time else "",
            order.remark,
            _fmt(order.created_at),
        ]
        for order, technician_name in rows
    ]
    return headers, data
