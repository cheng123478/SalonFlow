"""Excel 导出：用 openpyxl 内存生成 xlsx 字节。"""
from io import BytesIO

from openpyxl import Workbook


def build_workbook(headers: list[str], rows: list[list], sheet_name: str = "Sheet1") -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(headers)
    for row in rows:
        ws.append(row)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
