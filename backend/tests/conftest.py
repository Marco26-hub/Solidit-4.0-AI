from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy import text

from app.common import ratelimit
from app.db.session import engine
from app.main import app


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    # each test starts with a clean limiter so repeated registrations don't 429
    ratelimit.reset()
    yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def require_db():
    """Skip the test if PostgreSQL is not reachable. Disposes the pool so each
    test gets connections bound to the current event loop (CI-safe)."""
    try:
        await engine.dispose()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"PostgreSQL not available: {exc}")
    yield
