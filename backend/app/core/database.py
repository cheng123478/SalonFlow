"""数据库连接：SQLAlchemy 2.0 异步引擎 + 会话工厂。"""
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.sql_echo,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：为每个请求提供一个数据库会话。"""
    async with async_session() as session:
        yield session
