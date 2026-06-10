from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_tenant_principal, require_role
from app.devices import service
from app.devices.schemas import CalibrationUpload, DeviceOut, DeviceRegister

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])

_WRITE_ROLES = require_role("company_admin", "lab_manager")


@router.get("", response_model=list[DeviceOut])
async def list_devices(
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[DeviceOut]:
    rows = await service.list_devices(session, principal.company_id)
    return [DeviceOut.model_validate(d) for d in rows]


@router.post("/register", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
async def register_device(
    payload: DeviceRegister,
    principal: Principal = Depends(_WRITE_ROLES),
    session: AsyncSession = Depends(get_db),
) -> DeviceOut:
    device = await service.register_device(session, principal.company_id, payload)
    await record_audit(
        session,
        action="device.register",
        entity_type="device",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=device.id,
        payload={"hardware_uuid": device.hardware_uuid, "model": device.model},
    )
    return DeviceOut.model_validate(device)


@router.post("/{device_id}/calibrations", response_model=DeviceOut)
async def upload_calibration(
    device_id: uuid.UUID,
    payload: CalibrationUpload,
    principal: Principal = Depends(_WRITE_ROLES),
    session: AsyncSession = Depends(get_db),
) -> DeviceOut:
    device = await service.upload_calibration(session, principal.company_id, device_id, payload)
    await record_audit(
        session,
        action="device.calibration_upload",
        entity_type="device",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=device_id,
        payload={"illuminant": payload.illuminant},
    )
    return DeviceOut.model_validate(device)
