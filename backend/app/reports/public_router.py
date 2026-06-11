from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.deps import get_public_db
from app.reports import service

# unauthenticated public verification (the report QR points here)
router = APIRouter(prefix="/api/v1/public/reports", tags=["public"])


class PublicVerifyOut(BaseModel):
    valid: bool
    report_number: str | None = None
    company_name: str | None = None
    issued_at: str | None = None
    locked: bool | None = None
    sha256_hash: str | None = None


@router.get("/{report_id}/verify", response_model=PublicVerifyOut)
async def public_verify(
    report_id: uuid.UUID,
    h: str = Query(..., description="the report's SHA-256 seal from the QR/PDF"),
    session: AsyncSession = Depends(get_public_db),
) -> PublicVerifyOut:
    return PublicVerifyOut(**await service.public_verify(session, report_id, h))
