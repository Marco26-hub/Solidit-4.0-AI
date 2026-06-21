"""Spectral estimation API (R&D). Everything here is STIMATA and excluded from
the accredited report (project rule 7)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.deps import Principal, get_db, get_tenant_principal
from app.spectral import service
from app.spectral.schemas import (
    EstimateRequest,
    Illuminant,
    MetamerismRequest,
    MetamerismResult,
    ReflectanceEstimate,
    RenderRequest,
    RenderResult,
    ResultSpectralOut,
)
from app.vision.spectral import render_under_illuminant

router = APIRouter(prefix="/api/v1/spectral", tags=["spectral"])


@router.post("/estimate", response_model=ReflectanceEstimate)
async def estimate(
    body: EstimateRequest,
    principal: Principal = Depends(get_tenant_principal),
) -> ReflectanceEstimate:
    # the estimator may call out to a remote model (httpx, sync) — keep it off the
    # event loop so a slow Spark box can't stall other requests
    out = await run_in_threadpool(
        service.estimate_lab,
        [body.lab.L, body.lab.a, body.lab.b],
        illuminant=body.illuminant,
        observer=body.observer,
    )
    return ReflectanceEstimate.model_validate(out)


@router.post("/render-under", response_model=RenderResult)
async def render_under(
    body: RenderRequest,
    principal: Principal = Depends(get_tenant_principal),
) -> RenderResult:
    out = render_under_illuminant(body.reflectance, body.illuminant, observer=body.observer)
    return RenderResult.model_validate(out)


@router.post("/metamerism", response_model=MetamerismResult)
async def metamerism(
    body: MetamerismRequest,
    principal: Principal = Depends(get_tenant_principal),
) -> MetamerismResult:
    out = await run_in_threadpool(
        service.metamerism,
        [body.lab_reference.L, body.lab_reference.a, body.lab_reference.b],
        [body.lab_sample.L, body.lab_sample.a, body.lab_sample.b],
        reference_illuminant=body.reference_illuminant,
        observer=body.observer,
    )
    return MetamerismResult.model_validate(out)


@router.get("/measurement-results/{result_id}", response_model=ResultSpectralOut)
async def estimate_for_result(
    result_id: uuid.UUID,
    illuminant: Illuminant = "D65",
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> ResultSpectralOut:
    out = await service.estimate_for_result(
        session, principal.company_id, result_id, illuminant=illuminant
    )
    return ResultSpectralOut.model_validate(out)
