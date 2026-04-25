from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.models import Base


settings = get_settings()
engine = create_async_engine(settings.resolved_database_url, future=True, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        if settings.resolved_database_url.startswith("postgresql"):
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)


async def db_ping() -> bool:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return True

