from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError, NotFoundError
from app.db.models import ValidationRun, ValidationSample
from app.validation.schemas import ValidationRunCreate, ValidationSampleCreate

# indicative acceptance threshold (the spec suggests 90–95% within ±0.5 grade)
ACCEPT_PCT_WITHIN_HALF = 90.0


def compute_metrics(samples: list[ValidationSample]) -> dict:
    """Statistics of software grade vs reference grade over the campaign.
    Pure + testable. Only samples with BOTH grades present are scored."""
    pairs = [
        (float(s.software_grade), float(s.reference_grade))
        for s in samples
        if s.software_grade is not None and s.reference_grade is not None
    ]
    n = len(pairs)
    if n == 0:
        return {"n": 0, "scored": 0, "note": "nessun campione con entrambi i gradi"}

    devs = [sw - ref for sw, ref in pairs]
    abs_devs = [abs(d) for d in devs]
    within_half = sum(1 for d in abs_devs if d <= 0.5)
    pct_within = round(100.0 * within_half / n, 1)
    mean_abs = round(sum(abs_devs) / n, 3)
    bias = round(sum(devs) / n, 3)
    rmse = round((sum(d * d for d in devs) / n) ** 0.5, 3)
    return {
        "n": len(samples),
        "scored": n,
        "mean_abs_grade_dev": mean_abs,
        "pct_within_half_grade": pct_within,
        "max_abs_grade_dev": round(max(abs_devs), 2),
        "bias": bias,
        "rmse": rmse,
        "acceptance_threshold_pct": ACCEPT_PCT_WITHIN_HALF,
        "indicative_pass": pct_within >= ACCEPT_PCT_WITHIN_HALF,
    }


async def create_run(
    session: AsyncSession, company_id: uuid.UUID, data: ValidationRunCreate
) -> ValidationRun:
    run = ValidationRun(company_id=company_id, dataset_ref=data.name, status="pending")
    session.add(run)
    await session.flush()
    return run


async def list_runs(session: AsyncSession, company_id: uuid.UUID) -> list[ValidationRun]:
    return list(
        (
            await session.execute(
                select(ValidationRun)
                .where(ValidationRun.company_id == company_id)
                .order_by(ValidationRun.created_at.desc())
            )
        )
        .scalars()
        .all()
    )


async def get_run(
    session: AsyncSession, company_id: uuid.UUID, run_id: uuid.UUID
) -> ValidationRun:
    run = (
        await session.execute(
            select(ValidationRun).where(
                ValidationRun.id == run_id, ValidationRun.company_id == company_id
            )
        )
    ).scalar_one_or_none()
    if run is None:
        raise NotFoundError("Validation run not found")
    return run


async def list_samples(
    session: AsyncSession, company_id: uuid.UUID, run_id: uuid.UUID
) -> list[ValidationSample]:
    return list(
        (
            await session.execute(
                select(ValidationSample)
                .where(
                    ValidationSample.company_id == company_id,
                    ValidationSample.validation_run_id == run_id,
                )
                .order_by(ValidationSample.created_at)
            )
        )
        .scalars()
        .all()
    )


async def add_sample(
    session: AsyncSession,
    company_id: uuid.UUID,
    run_id: uuid.UUID,
    data: ValidationSampleCreate,
) -> ValidationSample:
    run = await get_run(session, company_id, run_id)
    if run.status == "computed":
        raise AppError(
            "Campagna già calcolata: ricalcola dopo aver aggiunto campioni.",
            code="run_computed",
        )
    sample = ValidationSample(
        company_id=company_id,
        validation_run_id=run_id,
        sample_code=data.sample_code,
        fiber=data.fiber,
        reference_method=data.reference_method,
        software_grade=data.software_grade,
        reference_grade=data.reference_grade,
        software_delta_e=data.software_delta_e,
        reference_delta_e=data.reference_delta_e,
    )
    session.add(sample)
    await session.flush()
    return sample


async def compute_run(
    session: AsyncSession, company_id: uuid.UUID, run_id: uuid.UUID
) -> ValidationRun:
    run = await get_run(session, company_id, run_id)
    samples = await list_samples(session, company_id, run_id)
    run.metrics = compute_metrics(samples)
    run.status = "computed"
    await session.flush()
    return run
