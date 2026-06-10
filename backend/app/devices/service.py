from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError, NotFoundError
from app.db.models import Device
from app.devices.schemas import CalibrationUpload, DeviceRegister


async def list_devices(session: AsyncSession, company_id: uuid.UUID) -> list[Device]:
    stmt = select(Device).where(Device.company_id == company_id).order_by(Device.created_at)
    return list((await session.execute(stmt)).scalars().all())


async def register_device(
    session: AsyncSession, company_id: uuid.UUID, data: DeviceRegister
) -> Device:
    device = Device(
        company_id=company_id,
        name=data.name or data.model or data.hardware_uuid,
        hardware_uuid=data.hardware_uuid,
        model=data.model,
        os_version=data.os_version,
        mdm_managed=data.mdm_managed,
    )
    session.add(device)
    try:
        async with session.begin_nested():  # SAVEPOINT: keep the txn usable on conflict
            await session.flush()
    except IntegrityError as exc:
        raise ConflictError("Device already registered for this company") from exc
    return device


async def get_device(session: AsyncSession, company_id: uuid.UUID, device_id: uuid.UUID) -> Device:
    stmt = select(Device).where(Device.id == device_id, Device.company_id == company_id)
    device = (await session.execute(stmt)).scalar_one_or_none()
    if device is None:
        raise NotFoundError("Device not found")
    return device


async def upload_calibration(
    session: AsyncSession,
    company_id: uuid.UUID,
    device_id: uuid.UUID,
    data: CalibrationUpload,
) -> Device:
    device = await get_device(session, company_id, device_id)
    matrix_payload = {"matrix": data.matrix, "profile": data.profile}
    if data.illuminant == "D65":
        device.active_d65_matrix = matrix_payload
    else:
        device.active_tl84_matrix = matrix_payload
    # keep a small marker in the calibration profile
    profile = dict(device.calibration_profile or {})
    profile[f"last_calibration_{data.illuminant.lower()}"] = data.profile
    device.calibration_profile = profile
    await session.flush()
    return device
