"""Append-only audit log writer.

The ``audit_log`` table is append-only: the ``solidita_app`` role is granted
INSERT/SELECT only (no UPDATE/DELETE — enforced in the migration). This helper
just inserts a row inside the caller's transaction/tenant context.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_INSERT = text(
    """
    INSERT INTO audit_log (company_id, actor_user_id, action, entity_type, entity_id, payload)
    VALUES (:company_id, :actor_user_id, :action, :entity_type, :entity_id, CAST(:payload AS jsonb))
    """
)


async def record_audit(
    session: AsyncSession,
    *,
    action: str,
    entity_type: str,
    company_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
    entity_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    import json

    await session.execute(
        _INSERT,
        {
            "company_id": str(company_id) if company_id else None,
            "actor_user_id": str(actor_user_id) if actor_user_id else None,
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id else None,
            "payload": json.dumps(payload or {}),
        },
    )
