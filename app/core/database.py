"""Async SQLAlchemy 2.0 Database Engine & Session Dependency (app/core/database.py).

Enforces Cloud SQL PostgreSQL 16 (`asyncpg`) in production and Testcontainers
PostgreSQL 16 (`pgvector/pgvector:pg16`) in CI/integration tests.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.models import Base

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db(target_engine: AsyncEngine | None = None) -> None:
    """Initializes the 6 canonical PostgreSQL 16 tables defined in app/core/models.py."""
    active_engine = target_engine or engine
    async with active_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency injecting an isolated async PostgreSQL 16 session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
