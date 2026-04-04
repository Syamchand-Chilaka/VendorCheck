"""SQLAlchemy async engine and session factory for RDS PostgreSQL."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.database_url
        # Convert postgresql:// to postgresql+asyncpg:// for async
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("sqlite://"):
            url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        _engine = create_async_engine(
            url, echo=(settings.app_env == "development"))
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(), expire_on_commit=False)
    return _session_factory


async def get_db() -> AsyncSession:
    """Yield an async DB session. Used as a FastAPI dependency."""
    factory = get_session_factory()
    async with factory() as session:
        yield session


def reset_engine():
    """Reset engine and session factory. Used in tests."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
