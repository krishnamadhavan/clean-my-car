"""Async SQLAlchemy engine and session factory."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()


def create_engine() -> AsyncEngine:
    """Build the async engine.

    Tests use ``NullPool`` so connections are not reused across event loops
    (avoids asyncpg "Future attached to a different loop" with TestClient).
    """
    kwargs: dict = {
        "echo": settings.debug,
        "pool_pre_ping": True,
    }
    if settings.app_env.lower() in {"test", "testing"}:
        kwargs["poolclass"] = NullPool
    return create_async_engine(settings.async_database_url, **kwargs)


engine = create_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a request-scoped DB session.

    Callers that mutate data should commit explicitly (or rely on a service layer).
    """
    async with AsyncSessionLocal() as session:
        yield session


async def dispose_engine() -> None:
    await engine.dispose()
