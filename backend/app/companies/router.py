from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_tenant_principal, require_role
from app.companies import service
from app.companies.schemas import (
    AuthorizationCreate,
    AuthorizationOut,
    CompanyOut,
    CompanyUpdate,
    MemberCreate,
    MemberOut,
)

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])

_ADMIN = require_role("company_admin")
_TEAM_VIEW = require_role("company_admin", "lab_manager")


@router.get("/me", response_model=CompanyOut)
async def get_my_company(
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> CompanyOut:
    company = await service.get_company(session, principal.company_id)
    return CompanyOut.model_validate(company)


# ── Team members (operator→admin approval flow needs real accounts) ──────────


@router.get("/members", response_model=list[MemberOut])
async def list_members(
    principal: Principal = Depends(_TEAM_VIEW),
    session: AsyncSession = Depends(get_db),
) -> list[MemberOut]:
    rows = await service.list_members(session, principal.company_id)
    return [MemberOut.model_validate(r) for r in rows]


@router.post("/members", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
async def add_member(
    data: MemberCreate,
    principal: Principal = Depends(_ADMIN),
    session: AsyncSession = Depends(get_db),
) -> MemberOut:
    member = await service.add_member(session, principal.company_id, data)
    await record_audit(
        session,
        action="company.member_added",
        entity_type="company_membership",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=member["user_id"],
        payload={"email": member["email"], "role": member["role"]},
    )
    return MemberOut.model_validate(member)


@router.delete("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    user_id: uuid.UUID,
    principal: Principal = Depends(_ADMIN),
    session: AsyncSession = Depends(get_db),
) -> None:
    await service.remove_member(session, principal.company_id, user_id, principal.user_id)
    await record_audit(
        session,
        action="company.member_removed",
        entity_type="company_membership",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=user_id,
        payload={},
    )


# ── Operator authorizations (ISO 17025 §6.2 personnel register) ───────────────


@router.get("/authorizations", response_model=list[AuthorizationOut])
async def list_authorizations(
    principal: Principal = Depends(_TEAM_VIEW),
    session: AsyncSession = Depends(get_db),
) -> list[AuthorizationOut]:
    rows = await service.list_authorizations(session, principal.company_id)
    return [AuthorizationOut.model_validate(r) for r in rows]


@router.post(
    "/authorizations", response_model=AuthorizationOut, status_code=status.HTTP_201_CREATED
)
async def add_authorization(
    data: AuthorizationCreate,
    principal: Principal = Depends(_TEAM_VIEW),
    session: AsyncSession = Depends(get_db),
) -> AuthorizationOut:
    auth = await service.add_authorization(session, principal.company_id, data, principal.user_id)
    await record_audit(
        session,
        action="company.operator_authorized",
        entity_type="operator_authorization",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=auth["id"],
        payload={
            "user_id": str(auth["user_id"]),
            "method_code": auth["method_code"],
            "valid_until": str(auth["valid_until"]) if auth["valid_until"] else None,
        },
    )
    return AuthorizationOut.model_validate(auth)


@router.post("/authorizations/{auth_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_authorization(
    auth_id: uuid.UUID,
    principal: Principal = Depends(_TEAM_VIEW),
    session: AsyncSession = Depends(get_db),
) -> None:
    await service.revoke_authorization(session, principal.company_id, auth_id)
    await record_audit(
        session,
        action="company.operator_authorization_revoked",
        entity_type="operator_authorization",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=auth_id,
        payload={},
    )


@router.patch("/{company_id}", response_model=CompanyOut)
async def update_company(
    company_id: uuid.UUID,
    payload: CompanyUpdate,
    principal: Principal = Depends(require_role("company_admin")),
    session: AsyncSession = Depends(get_db),
) -> CompanyOut:
    service.ensure_same_company(principal.company_id, company_id)
    company = await service.update_company(session, company_id, payload)
    await record_audit(
        session,
        action="company.update",
        entity_type="company",
        company_id=company_id,
        actor_user_id=principal.user_id,
        entity_id=company_id,
        payload=payload.model_dump(exclude_none=True),
    )
    return CompanyOut.model_validate(company)
