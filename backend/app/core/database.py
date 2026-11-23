from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Create async engine with bounded connection pool configuration
engine_kwargs = {
    "echo": (settings.ENVIRONMENT == "development"),
    "future": True,
    "pool_pre_ping": True,
}
if "sqlite" not in settings.DATABASE_URL:
    engine_kwargs.update(
        {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
        }
    )

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)


# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection helper yielding an async SQLAlchemy session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db_pool_status() -> dict[str, Any]:
    """Retrieve database connection pool saturation metrics."""
    sync_engine = getattr(engine, "sync_engine", engine)
    pool = getattr(sync_engine, "pool", None)
    if pool is None:
        return {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "checked_in": 0,
            "checked_out": 0,
            "overflow": 0,
            "total_active": 0,
            "total_capacity": settings.DB_POOL_SIZE + settings.DB_MAX_OVERFLOW,
            "saturation_pct": 0.0,
        }

    size = pool.size() if hasattr(pool, "size") else settings.DB_POOL_SIZE
    checked_in = pool.checkedin() if hasattr(pool, "checkedin") else 0
    checked_out = pool.checkedout() if hasattr(pool, "checkedout") else 0
    overflow = pool.overflow() if hasattr(pool, "overflow") else 0
    total_active = checked_out
    total_capacity = size + settings.DB_MAX_OVERFLOW
    saturation_pct = round((total_active / total_capacity * 100), 2) if total_capacity > 0 else 0.0

    return {
        "pool_size": size,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "checked_in": checked_in,
        "checked_out": checked_out,
        "overflow": overflow,
        "total_active": total_active,
        "total_capacity": total_capacity,
        "saturation_pct": saturation_pct,
    }

