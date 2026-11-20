"""报表接口：工作台汇总 + 预约统计 + Excel 导出。"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.response import success
from app.services import report as service
from app.services.excel import build_workbook

router = APIRouter(
    prefix="/report",
    tags=["报表"],
    dependencies=[Depends(get_current_user)],
)

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _xlsx_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    return success(await service.overview(db))


@router.get("/reserve-stats")
async def reserve_stats(db: AsyncSession = Depends(get_db)):
    data = {
        "status": await service.reserve_status_stats(db),
        "technician": await service.reserve_technician_stats(db),
        "member_monthly": await service.member_monthly_stats(db),
    }
    return success(data)


@router.get("/export/members")
async def export_members(db: AsyncSession = Depends(get_db)):
    headers, rows = await service.export_members(db)
    return _xlsx_response(build_workbook(headers, rows, "会员"), "members.xlsx")


@router.get("/export/reserves")
async def export_reserves(db: AsyncSession = Depends(get_db)):
    headers, rows = await service.export_reserves(db)
    return _xlsx_response(build_workbook(headers, rows, "预约"), "reserves.xlsx")


@router.get("/export/inventory")
async def export_inventory(db: AsyncSession = Depends(get_db)):
    headers, rows = await service.export_inventory(db)
    return _xlsx_response(build_workbook(headers, rows, "库存"), "inventory.xlsx")


@router.get("/export/orders")
async def export_orders(db: AsyncSession = Depends(get_db)):
    headers, rows = await service.export_orders(db)
    return _xlsx_response(build_workbook(headers, rows, "订单"), "orders.xlsx")


@router.get("/revenue")
async def revenue(db: AsyncSession = Depends(get_db)):
    data = {
        "summary": await service.revenue_summary(db),
        "daily": await service.revenue_daily_stats(db),
        "technician": await service.revenue_technician_stats(db),
    }
    return success(data)
