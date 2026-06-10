from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_tenant_principal, require_role
from app.companies import service
from app.companies.schemas import CompanyOut, CompanyUpdate

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


@router.get("/me", response_model=CompanyOut)
async def get_my_company(
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> CompanyOut:
    company = await service.get_company(session, principal.company_id)
    return CompanyOut.model_validate(company)


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
