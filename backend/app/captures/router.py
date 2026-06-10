from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.captures import service
from app.captures.schemas import CaptureSessionCreate, CaptureSessionOut, ImageAssetOut
from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_tenant_principal, require_role
from app.test_jobs.schemas import MeasurementResultOut

router = APIRouter(prefix="/api/v1/capture-sessions", tags=["captures"])

_OPERATE = require_role("company_admin", "lab_manager", "operator")


@router.post("", response_model=CaptureSessionOut, status_code=status.HTTP_201_CREATED)
async def create_capture_session(
    payload: CaptureSessionCreate,
    principal: Principal = Depends(_OPERATE),
    session: AsyncSession = Depends(get_db),
) -> CaptureSessionOut:
    cs = await service.create_session(session, principal.company_id, principal.user_id, payload)
    await record_audit(
        session,
        action="capture.session_create",
        entity_type="capture_session",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=cs.id,
        payload={"capture_type": cs.capture_type, "method": cs.test_method_code},
    )
    return CaptureSessionOut.model_validate(cs)


@router.post(
    "/{session_id}/images", response_model=ImageAssetOut, status_code=status.HTTP_201_CREATED
)
async def upload_image(
    session_id: uuid.UUID,
    file: UploadFile = File(...),
    asset_type: str = Query(default="multifiber_after"),
    principal: Principal = Depends(_OPERATE),
    session: AsyncSession = Depends(get_db),
) -> ImageAssetOut:
    data = await file.read()
    asset = await service.add_image(
        session,
        principal.company_id,
        session_id,
        asset_type,
        data,
        file.filename or "image",
        file.content_type,
    )
    await record_audit(
        session,
        action="capture.image_upload",
        entity_type="image_asset",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=asset.id,
        payload={"asset_type": asset.asset_type, "sha256": asset.sha256_hash},
    )
    return ImageAssetOut.model_validate(asset)


@router.get("/{session_id}/images", response_model=list[ImageAssetOut])
async def list_images(
    session_id: uuid.UUID,
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[ImageAssetOut]:
    rows = await service.list_images(session, principal.company_id, session_id)
    return [ImageAssetOut.model_validate(a) for a in rows]


@router.post(
    "/{session_id}/analyze",
    response_model=MeasurementResultOut,
    status_code=status.HTTP_201_CREATED,
)
async def analyze(
    session_id: uuid.UUID,
    principal: Principal = Depends(_OPERATE),
    session: AsyncSession = Depends(get_db),
) -> MeasurementResultOut:
    result = await service.analyze(session, principal.company_id, session_id)
    await record_audit(
        session,
        action="capture.analyze",
        entity_type="measurement_result",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=result.id,
        payload={"overall_pass": result.pass_fail.get("overall_pass")},
    )
    return MeasurementResultOut.model_validate(result)
