from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.accreditation import service
from app.common.deps import Principal, get_db, get_tenant_principal

router = APIRouter(prefix="/api/v1/accreditation", tags=["accreditation"])


@router.get("/readiness")
async def readiness(
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return await service.readiness(session, principal.company_id)
