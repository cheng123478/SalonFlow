"""FastAPI 入口：应用装配、全局异常处理、启动建表与种子账号。"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, async_session, engine
from app.core.response import fail
from app.core.security import hash_password
from app.models import User


async def init_db():
    """启动时建表 + 写入默认店长账号（admin / admin123）。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none() is None:
            db.add(
                User(
                    username="admin",
                    password_hash=hash_password("admin123"),
                    real_name="店长",
                    user_type="owner",
                    phone="",
                )
            )
            await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# 头像等上传文件的静态服务（保存到 upload_dir 下直接访问）
UPLOAD_DIR = Path(settings.upload_dir).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


# ---- 统一异常处理：全部返回 {code, message, data} ----
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content=fail(exc.status_code, str(exc.detail)))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content=fail(422, "参数校验失败"))


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content=fail(409, "数据冲突：记录已存在或关联数据不完整"))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content=fail(500, "服务器内部错误"))


@app.get("/api/health")
async def health():
    return {"code": 0, "message": "ok", "data": {"status": "healthy"}}
