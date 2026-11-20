"""API 总路由：统一挂载到 /api 前缀下。"""
from fastapi import APIRouter

from app.api.v1 import auth, chat, inventory, knowledge, member, order, report, reserve, technician, upload, user

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(member.router)
api_router.include_router(technician.router)
api_router.include_router(reserve.router)
api_router.include_router(order.router)
api_router.include_router(inventory.router)
api_router.include_router(report.router)
api_router.include_router(chat.router)
api_router.include_router(knowledge.router)
api_router.include_router(upload.router)
