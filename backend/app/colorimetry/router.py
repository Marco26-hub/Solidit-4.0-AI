"""Camera characterisation + measurement-uncertainty API (colorimeter-grade
colour path toward an accreditable scope). Tenant-scoped, compute-only."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from app.colorimetry import service
from app.colorimetry.schemas import (
    ApplyRequest,
    ApplyResponse,
    CharacterizeRequest,
    CharacterizeResponse,
    UncertaintyRequest,
    UncertaintyResponse,
)
from app.common.deps import Principal, get_tenant_principal

router = APIRouter(prefix="/api/v1/colorimetry", tags=["colorimetry"])


@router.post("/characterize", response_model=CharacterizeResponse)
async def characterize(
    body: CharacterizeRequest,
    principal: Principal = Depends(get_tenant_principal),
) -> CharacterizeResponse:
    out = await run_in_threadpool(
        service.characterize,
        body.patches,
        degree=body.degree,
        reference_lab=body.reference_lab,
    )
    return CharacterizeResponse.model_validate(out)


@router.post("/apply", response_model=ApplyResponse)
async def apply(
    body: ApplyRequest,
    principal: Principal = Depends(get_tenant_principal),
) -> ApplyResponse:
    out = service.apply(body.matrix, body.rgb, degree=body.degree)
    return ApplyResponse.model_validate(out)


@router.post("/uncertainty", response_model=UncertaintyResponse)
async def uncertainty(
    body: UncertaintyRequest,
    principal: Principal = Depends(get_tenant_principal),
) -> UncertaintyResponse:
    components = (
        [c.model_dump(exclude_none=True) for c in body.components]
        if body.components
        else {
            "repeatability": body.repeatability,
            "characterisation": body.characterisation,
            "reproducibility": body.reproducibility,
            "reference": body.reference,
        }
    )
    out = service.uncertainty(
        components,
        coverage_factor=body.coverage_factor,
        confidence_level=body.confidence_level,
        measured_value=body.measured_value,
        tolerance_limit=body.tolerance_limit,
        decision_direction=body.decision_direction,
    )
    return UncertaintyResponse.model_validate(out)
