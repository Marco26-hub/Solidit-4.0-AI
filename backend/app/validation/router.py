from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_tenant_principal, require_role
from app.db.models import ValidationRun
from app.validation import service
from app.validation.schemas import (
    ValidationRunCreate,
    ValidationRunDetail,
    ValidationRunOut,
    ValidationSampleCreate,
    ValidationSampleOut,
)

router = APIRouter(prefix="/api/v1/validation-runs", tags=["validation"])

_MANAGE = require_role("company_admin", "lab_manager")


def _run_out(run: ValidationRun) -> ValidationRunOut:
    return ValidationRunOut(
        id=run.id,
        name=run.dataset_ref,
        status=run.status,
        metrics=run.metrics or {},
        created_at=run.created_at,
    )


@router.post("", response_model=ValidationRunOut, status_code=status.HTTP_201_CREATED)
async def create_run(
    data: ValidationRunCreate,
    principal: Principal = Depends(_MANAGE),
    session: AsyncSession = Depends(get_db),
) -> ValidationRunOut:
    run = await service.create_run(session, principal.company_id, data)
    await record_audit(
        session,
        action="validation.run_create",
        entity_type="validation_run",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=run.id,
        payload={"name": data.name},
    )
    return _run_out(run)


@router.get("", response_model=list[ValidationRunOut])
async def list_runs(
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[ValidationRunOut]:
    return [_run_out(r) for r in await service.list_runs(session, principal.company_id)]


@router.get("/{run_id}", response_model=ValidationRunDetail)
async def get_run(
    run_id: uuid.UUID,
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> ValidationRunDetail:
    run = await service.get_run(session, principal.company_id, run_id)
    samples = await service.list_samples(session, principal.company_id, run_id)
    return ValidationRunDetail(
        id=run.id,
        name=run.dataset_ref,
        status=run.status,
        metrics=run.metrics or {},
        created_at=run.created_at,
        samples=[ValidationSampleOut.model_validate(s) for s in samples],
    )


@router.post(
    "/{run_id}/samples", response_model=ValidationSampleOut, status_code=status.HTTP_201_CREATED
)
async def add_sample(
    run_id: uuid.UUID,
    data: ValidationSampleCreate,
    principal: Principal = Depends(_MANAGE),
    session: AsyncSession = Depends(get_db),
) -> ValidationSampleOut:
    sample = await service.add_sample(session, principal.company_id, run_id, data)
    return ValidationSampleOut.model_validate(sample)


@router.post("/{run_id}/compute", response_model=ValidationRunOut)
async def compute_run(
    run_id: uuid.UUID,
    principal: Principal = Depends(_MANAGE),
    session: AsyncSession = Depends(get_db),
) -> ValidationRunOut:
    run = await service.compute_run(session, principal.company_id, run_id)
    await record_audit(
        session,
        action="validation.run_compute",
        entity_type="validation_run",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=run.id,
        payload={"metrics": run.metrics},
    )
    return _run_out(run)
