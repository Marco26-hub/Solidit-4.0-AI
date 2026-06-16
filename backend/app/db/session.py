"""Async engine + session factory.

The app connects as the NON-superuser ``solidita_app`` role, so PostgreSQL RLS
is enforced. Tenant context (GUCs) is applied per-request by the dependencies in
``app.common.deps`` via ``app.common.rls.apply_rls``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

SSL_REQUIRED_MODES = {"allow", "prefer", "require", "verify-ca", "verify-full"}


def _prepare_async_engine_config(database_url: str) -> tuple[str, dict[str, Any]]:
    """Translate common managed-Postgres URL params for asyncpg.

    Providers such as Neon expose URLs with ``sslmode=require``. psycopg accepts
    that parameter directly, while asyncpg expects ``ssl`` in connect_args.
    """
    url = make_url(database_url)
    connect_args: dict[str, Any] = {}

    if url.drivername.endswith("+asyncpg") and "sslmode" in url.query:
        query = dict(url.query)
        raw_sslmode = query.pop("sslmode")
        sslmode = raw_sslmode[-1] if isinstance(raw_sslmode, tuple) else raw_sslmode
        sslmode = str(sslmode).lower()

        if sslmode in SSL_REQUIRED_MODES:
            connect_args["ssl"] = True
        elif sslmode == "disable":
            connect_args["ssl"] = False
        else:
            raise ValueError(f"Unsupported asyncpg sslmode: {sslmode}")

        url = url.set(query=query)

    return url.render_as_string(hide_password=False), connect_args


_database_url, _connect_args = _prepare_async_engine_config(settings.database_url)

engine = create_async_engine(
    _database_url,
    connect_args=_connect_args,
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
