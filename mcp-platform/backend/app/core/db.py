from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(
    settings.database_url,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a short-lived database session for an API request."""
    async with SessionLocal() as session:
        yield session
