"""Async database engine, session factory, and FastAPI dependency."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from sqlalchemy import event

from app.entities.base import Base  # noqa: F401 — ensure all models are imported
import app.entities  # noqa: F401 — register all models on Base.metadata

DATABASE_URL = "sqlite+aiosqlite:///./pisces.db"

_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False, "timeout": 30},
)


@event.listens_for(_engine.sync_engine, "connect")
def _set_sqlite_wal(dbapi_conn, connection_record):  # noqa: ANN001
    """Enable WAL journal mode for better concurrent read/write support."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

async_session_maker = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_all_tables() -> None:
    """Create all tables (used during app startup / testing)."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DbDep = Annotated[AsyncSession, Depends(_get_db)]

