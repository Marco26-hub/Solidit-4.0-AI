from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import tokens
from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_principal
from app.common.schemas import Message
from app.db.models import Company, CompanyMembership, User

router = APIRouter(prefix="/api/v1/account", tags=["account"])


class MembershipExport(BaseModel):
    company_id: uuid.UUID
    company: str
    role: str


class AccountExport(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str | None
    created_at: datetime
    last_login_at: datetime | None
    memberships: list[MembershipExport]


@router.get("/export", response_model=AccountExport)
async def export_my_data(
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> AccountExport:
    """GDPR data portability: the personal data we hold about the caller."""
    user = await session.get(User, principal.user_id)
    rows = (
        await session.execute(
            select(Company.id, Company.name, CompanyMembership.role)
            .join(CompanyMembership, CompanyMembership.company_id == Company.id)
            .where(CompanyMembership.user_id == principal.user_id)
        )
    ).all()
    return AccountExport(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        memberships=[MembershipExport(company_id=r[0], company=r[1], role=r[2]) for r in rows],
    )


@router.post("/delete", response_model=Message)
async def request_account_deletion(
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> Message:
    """GDPR erasure request: deactivate the account and revoke all sessions.
    Hard deletion is performed per the retention policy (see docs/legal)."""
    user = await session.get(User, principal.user_id)
    if user is not None:
        user.is_active = False
    await tokens.revoke_user(session, principal.user_id)
    if principal.company_id is not None:
        await record_audit(
            session,
            action="account.delete_request",
            entity_type="user",
            company_id=principal.company_id,
            actor_user_id=principal.user_id,
            entity_id=principal.user_id,
        )
    return Message(
        message="Account deactivated and all sessions revoked. "
        "Hard erasure follows the retention policy."
    )
