"""
database/session.py

Async SQLAlchemy engine and session factory.

Design decisions
----------------
- AsyncEngine is created once and shared for the process lifetime.
- AsyncSessionLocal is a session factory (not a session itself).
- ``get_db_session`` is a FastAPI dependency that yields one session per
  request and ensures it is always closed, even on exception.
- The engine is disposed in the lifespan shutdown hook (core/lifespan.py).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings
from uuid import uuid4
from asyncpg import Connection


class UniqueNameConnection(Connection):
    def _get_unique_id(self, prefix: str) -> str:
        return f"__asyncpg_{prefix}_{uuid4()}__"


# ─────────────────────────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────────────────────────

engine_args = {
    "echo": settings.debug,
    "pool_pre_ping": True,
    "future": True,
}

if not settings.database_url.startswith("sqlite"):
    engine_args["pool_size"] = settings.database_pool_size
    engine_args["max_overflow"] = settings.database_max_overflow
    engine_args["connect_args"] = {
        "connection_class": UniqueNameConnection,
        "statement_cache_size": 0,
    }

engine: AsyncEngine = create_async_engine(settings.database_url, **engine_args)

# ─────────────────────────────────────────────────────────────────────────────
# Session factory
# ─────────────────────────────────────────────────────────────────────────────

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # prevents lazy-loading after commit
)


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI dependency
# ─────────────────────────────────────────────────────────────────────────────


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a scoped AsyncSession for one HTTP request.

    The session is always closed in the ``finally`` block — even if the
    handler raises an exception or the client disconnects mid-stream.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
