"""Row Level Security helpers.

Tenant context is carried by two transaction-local PostgreSQL GUCs:

* ``app.current_user_id``    — the authenticated user (always set)
* ``app.current_company_id`` — the selected tenant (set when known)

We use ``set_config(key, value, is_local => true)`` (NOT ``SET``) because:
* it accepts bind parameters (``SET`` does not), avoiding SQL injection, and
* ``is_local => true`` scopes the value to the current transaction, so it can
  never leak across pooled connections (asyncpg / PgBouncer safe).

RLS policies read these with ``NULLIF(current_setting(key, true), '')::uuid`` so
an unset value becomes NULL and the policy FAILS CLOSED (no rows visible).
"""

from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_SET_CONFIG = text("SELECT set_config(:key, :value, true)")


async def apply_rls(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    company_id: uuid.UUID | None = None,
) -> None:
    """Set tenant GUCs on the current transaction. Must be called inside a
    transaction (the caller opens one before yielding the session)."""
    await session.execute(_SET_CONFIG, {"key": "app.current_user_id", "value": str(user_id)})
    await session.execute(
        _SET_CONFIG,
        {"key": "app.current_company_id", "value": str(company_id) if company_id else ""},
    )
