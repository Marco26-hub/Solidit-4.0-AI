"""Async engine + session factory.

The app connects as the NON-superuser ``solidita_app`` role, so PostgreSQL RLS
is enforced. Tenant context (GUCs) is applied per-request by the dependencies in
``app.common.deps`` via ``app.common.rls.apply_rls``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def raw_session() -> AsyncIterator[AsyncSession]:
    """A session with NO tenant context set (used only by auth login/refresh,
    which read the global ``users`` table). Do not use for tenant data."""
    async with SessionLocal() as session:
        yield session
