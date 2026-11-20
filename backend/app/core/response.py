"""统一响应结构：所有接口返回 {"code", "message", "data"}。"""
from typing import Any


def success(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}


def fail(code: int, message: str) -> dict:
    return {"code": code, "message": message, "data": None}
