"""Agent 工具：会员/库存/预约的只读查询 + 写操作方案生成。"""
from langchain_core.tools import tool
from sqlalchemy import or_, select

from app.agent import rag
from app.core.database import async_session
from app.models.inventory import Inventory
from app.models.member import Member
from app.models.reserve import Reserve


# ---------- 只读查询工具（直接执行） ----------

@tool
async def query_members(keyword: str = "") -> str:
    """按姓名或手机号搜索会员，返回会员列表（余额、标签、发质备注）。keyword 留空则返回最近会员。"""
    async with async_session() as db:
        stmt = select(Member).order_by(Member.id.desc())
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(or_(Member.name.like(like), Member.phone.like(like)))
        rows = (await db.execute(stmt)).scalars().all()
    if not rows:
        return "未找到匹配的会员。"
    lines = [f"共 {len(rows)} 位会员："]
    for m in rows:
        name = m.name or "未填姓名"
        lines.append(f"- {name}（{m.phone}）：余额 {m.balance}，标签 {m.tags or '无'}，发质 {m.hair_remark or '无'}")
    return "\n".join(lines)


@tool
async def query_inventory(keyword: str = "") -> str:
    """查询库存物料及低库存预警。keyword 可筛选物料名称。"""
    async with async_session() as db:
        stmt = select(Inventory).order_by(Inventory.id.desc())
        if keyword:
            stmt = stmt.where(Inventory.name.like(f"%{keyword}%"))
        rows = (await db.execute(stmt)).scalars().all()
    if not rows:
        return "未找到匹配的物料。"
    lines = [f"共 {len(rows)} 种物料："]
    for i in rows:
        warn = "（低库存）" if i.quantity < i.threshold else ""
        lines.append(f"- {i.name}：库存 {i.quantity}{i.unit}，安全阈值 {i.threshold}{warn}")
    return "\n".join(lines)


@tool
async def query_reservations(status: str = "", technician_id: int = 0, phone: str = "") -> str:
    """查询预约记录，可按状态(pending/confirmed/completed/cancelled)、技师ID、手机号筛选。"""
    async with async_session() as db:
        stmt = select(Reserve).order_by(Reserve.reserve_time.desc())
        if status:
            stmt = stmt.where(Reserve.status == status)
        if technician_id:
            stmt = stmt.where(Reserve.technician_id == technician_id)
        if phone:
            stmt = stmt.where(Reserve.phone.like(f"%{phone}%"))
        rows = (await db.execute(stmt)).scalars().all()
    if not rows:
        return "暂无符合条件的预约。"
    lines = [f"共 {len(rows)} 条预约："]
    for r in rows:
        lines.append(f"- [{r.status}] {r.reserve_time} 技师ID {r.technician_id}，{r.phone}，项目 {r.project or '未填'}")
    return "\n".join(lines)


# ---------- 写操作方案工具（只生成方案，不写库，待用户确认） ----------

@tool
async def propose_create_reserve(technician_id: int, phone: str, reserve_time: str, project: str = "") -> str:
    """为顾客起草预约方案（不真正写入）。reserve_time 用 'YYYY-MM-DDTHH:mm:ss' 格式。"""
    return f"预约方案：技师ID {technician_id}，手机号 {phone}，时间 {reserve_time}，项目 {project or '未填'}"


@tool
async def propose_create_member(phone: str, name: str = "", tags: str = "", hair_remark: str = "") -> str:
    """为顾客起草新增会员方案（不真正写入）。"""
    return f"新增会员方案：{name or '未填姓名'}（{phone}），标签 {tags or '无'}，发质 {hair_remark or '无'}"


@tool
async def propose_stock_change(inventory_id: int, change_type: str, quantity: int, remark: str = "") -> str:
    """起草出入库方案（不真正写入）。change_type 为 in(入库) 或 out(出库)。"""
    return f"出入库方案：物料ID {inventory_id}，{change_type}，数量 {quantity}，备注 {remark or '无'}"


# ---------- 知识库检索工具（走 rag_retriever 节点） ----------

@tool
async def search_knowledge(query: str) -> str:
    """在门店知识库中检索经营/护理专业知识（染发护理、会员运营、预约规范等）。回答专业问题前应先检索。"""
    hits = await rag.search(query, top_k=4)
    return rag.format_hits(hits)


# 工具名 -> (实现, 是否为写操作方案)
TOOLS = {
    "query_members": (query_members, False),
    "query_inventory": (query_inventory, False),
    "query_reservations": (query_reservations, False),
    "propose_create_reserve": (propose_create_reserve, True),
    "propose_create_member": (propose_create_member, True),
    "propose_stock_change": (propose_stock_change, True),
}

# 写方案工具名 -> 确认后实际执行的 action
PROPOSE_ACTION_MAP = {
    "propose_create_reserve": "create_reserve",
    "propose_create_member": "create_member",
    "propose_stock_change": "change_stock",
}
