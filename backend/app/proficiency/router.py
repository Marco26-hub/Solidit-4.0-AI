from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_tenant_principal, require_role
from app.proficiency import service
from app.proficiency.schemas import ProficiencyTestCreate, ProficiencyTestOut

router = APIRouter(prefix="/api/v1/proficiency-tests", tags=["proficiency"])

_MANAGE = require_role("company_admin", "lab_manager")


@router.post("", response_model=ProficiencyTestOut, status_code=status.HTTP_201_CREATED)
async def create_pt(
    data: ProficiencyTestCreate,
    principal: Principal = Depends(_MANAGE),
    session: AsyncSession = Depends(get_db),
) -> ProficiencyTestOut:
    pt = await service.create(session, principal.company_id, data)
    await record_audit(
        session,
        action="proficiency.create",
        entity_type="proficiency_test",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=pt.id,
        payload={"scheme": pt.scheme, "round": pt.round_label, "verdict": pt.verdict},
    )
    return ProficiencyTestOut.model_validate(pt)


@router.get("", response_model=list[ProficiencyTestOut])
async def list_pt(
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[ProficiencyTestOut]:
    return [
        ProficiencyTestOut.model_validate(p)
        for p in await service.list_all(session, principal.company_id)
    ]
