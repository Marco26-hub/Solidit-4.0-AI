from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.calibration import service
from app.calibration.schemas import CalibrationReferenceCreate, CalibrationReferenceOut
from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_tenant_principal, require_role
from app.db.models import CalibrationReference

router = APIRouter(prefix="/api/v1/calibration-references", tags=["calibration"])

_MANAGE = require_role("company_admin", "lab_manager")


def _out(ref: CalibrationReference) -> CalibrationReferenceOut:
    m = ref.meta or {}
    return CalibrationReferenceOut(
        id=ref.id,
        kind=ref.kind,
        code=ref.code,
        description=ref.description,
        certificate_number=ref.certificate_number,
        valid_from=ref.valid_from,
        valid_until=ref.valid_until,
        status=ref.status,
        reference_values=ref.reference_values,
        validity=service.compute_validity(ref),
        created_at=ref.created_at,
        subtype=m.get("subtype"),
        series=m.get("series"),
        standard=m.get("standard"),
        illuminants=m.get("illuminants"),
        lamp_hours=m.get("lamp_hours"),
        cert_illuminant=m.get("cert_illuminant"),
        cert_observer=m.get("cert_observer"),
        consumable_type=m.get("consumable_type"),
        patch_values=m.get("patches"),
    )


@router.post("", response_model=CalibrationReferenceOut, status_code=status.HTTP_201_CREATED)
async def create_reference(
    data: CalibrationReferenceCreate,
    principal: Principal = Depends(_MANAGE),
    session: AsyncSession = Depends(get_db),
) -> CalibrationReferenceOut:
    ref = await service.create_reference(session, principal.company_id, data)
    await record_audit(
        session,
        action="calibration.reference_create",
        entity_type="calibration_reference",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=ref.id,
        payload={"kind": ref.kind, "code": ref.code},
    )
    return _out(ref)


@router.get("", response_model=list[CalibrationReferenceOut])
async def list_references(
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[CalibrationReferenceOut]:
    return [_out(r) for r in await service.list_references(session, principal.company_id)]


@router.post("/{ref_id}/retire", response_model=CalibrationReferenceOut)
async def retire_reference(
    ref_id: uuid.UUID,
    principal: Principal = Depends(_MANAGE),
    session: AsyncSession = Depends(get_db),
) -> CalibrationReferenceOut:
    ref = await service.retire_reference(session, principal.company_id, ref_id)
    await record_audit(
        session,
        action="calibration.reference_retire",
        entity_type="calibration_reference",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=ref.id,
        payload={"kind": ref.kind, "code": ref.code},
    )
    return _out(ref)
