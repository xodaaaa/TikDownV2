from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.config import settings
from src.db.base import Base

# engine para la DB de negocio
engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.DATABASE_PATH}",
    poolclass=NullPool,
    connect_args={"check_same_thread": False},
)

# engine separado para el jobstore de APScheduler
scheduler_engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.SCHEDULER_DB_PATH}",
    poolclass=NullPool,
    connect_args={"check_same_thread": False},
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

scheduler_session_factory = async_sessionmaker(
    scheduler_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def get_scheduler_db() -> AsyncGenerator[AsyncSession, None]:
    async with scheduler_session_factory() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
