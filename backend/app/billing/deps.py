"""Plan-tier gating. Use to restrict premium endpoints (e.g. Vision) by the
company's account_tier. Example: Depends(require_tier("vision", "enterprise"))."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.deps import Principal, get_db, get_tenant_principal
from app.common.errors import ForbiddenError
from app.companies.service import get_company


def require_tier(*tiers: str) -> Callable[..., Coroutine[Any, Any, Principal]]:
    async def _dependency(
        principal: Principal = Depends(get_tenant_principal),
        session: AsyncSession = Depends(get_db),
    ) -> Principal:
        company = await get_company(session, principal.company_id)
        if company.account_tier not in tiers:
            raise ForbiddenError(
                f"This feature requires plan tier {', '.join(tiers)} "
                f"(current: {company.account_tier})."
            )
        return principal

    return _dependency
