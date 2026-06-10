from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.batches import service
from app.batches.schemas import BatchCreate, BatchOut, BatchStatusUpdate, StripProfileOut
from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_principal, get_tenant_principal, require_role

router = APIRouter(prefix="/api/v1/multifiber-batches", tags=["batch-zero"])

_WRITE_ROLES = require_role("company_admin", "lab_manager")


@router.get("/strip-profiles", response_model=list[StripProfileOut])
async def list_strip_profiles(
    _: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> list[StripProfileOut]:
    """Available multifiber strip standards (AATCC, ISO/UNI EN ISO 105-F10 DW/TV).
    Defined before /{batch_id} so the literal path takes precedence."""
    rows = await service.list_strip_profiles(session)
    return [StripProfileOut.model_validate(p) for p in rows]


@router.get("", response_model=list[BatchOut])
async def list_batches(
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[BatchOut]:
    rows = await service.list_batches(session, principal.company_id)
    return [BatchOut.model_validate(b) for b in rows]


@router.post("", response_model=BatchOut, status_code=status.HTTP_201_CREATED)
async def create_batch(
    payload: BatchCreate,
    principal: Principal = Depends(_WRITE_ROLES),
    session: AsyncSession = Depends(get_db),
) -> BatchOut:
    batch = await service.create_batch(session, principal.company_id, principal.user_id, payload)
    await record_audit(
        session,
        action="batch_zero.create",
        entity_type="multifiber_batch",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=batch.id,
        payload={"batch_code": batch.batch_code, "fibers": list(batch.reference_lab_values)},
    )
    return BatchOut.model_validate(batch)


@router.get("/{batch_id}", response_model=BatchOut)
async def get_batch(
    batch_id: uuid.UUID,
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> BatchOut:
    batch = await service.get_batch(session, principal.company_id, batch_id)
    return BatchOut.model_validate(batch)


@router.patch("/{batch_id}", response_model=BatchOut)
async def update_batch_status(
    batch_id: uuid.UUID,
    payload: BatchStatusUpdate,
    principal: Principal = Depends(_WRITE_ROLES),
    session: AsyncSession = Depends(get_db),
) -> BatchOut:
    batch = await service.update_status(session, principal.company_id, batch_id, payload.status)
    await record_audit(
        session,
        action="batch_zero.status",
        entity_type="multifiber_batch",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=batch_id,
        payload={"status": payload.status},
    )
    return BatchOut.model_validate(batch)
