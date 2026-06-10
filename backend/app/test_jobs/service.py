from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import NotFoundError
from app.db.models import BrandAcceptanceRule, MeasurementResult, TestJob, TestMethod
from app.test_jobs.schemas import ManualResultCreate, TestJobCreate

MANUAL_ALGO_VERSION = "manual-entry-0.1.0"


# ── Pure pass/fail evaluation (unit-testable, no DB) ────────────────────────────
def evaluate_pass_fail(rules: list[dict], method_code: str, fibers: dict[str, dict]) -> dict:
    """Evaluate measured fiber values against brand acceptance rules.

    rules: list of {test_method_code, fiber_code, max_delta_e, min_gray_scale_grade, severity}
    fibers: {fiber_code: {"delta_e": float|None, "gray_scale_grade": float|None}}
    A blocking violation fails the fiber (and the job). Warnings are recorded but
    do not fail. A job with no applicable rules is 'inconclusive' (overall False).
    """
    per_fiber: dict[str, dict] = {}
    violations: list[dict] = []
    any_rule_applied = False

    for fiber, meas in fibers.items():
        applicable = [
            r
            for r in rules
            if r["test_method_code"] == method_code and r.get("fiber_code") in (None, fiber)
        ]
        checks: list[dict] = []
        fiber_pass = True
        for r in applicable:
            severity = r.get("severity", "blocking")
            de = meas.get("delta_e")
            grade = meas.get("gray_scale_grade")
            if r.get("max_delta_e") is not None and de is not None:
                any_rule_applied = True
                ok = de <= r["max_delta_e"]
                checks.append(
                    {"metric": "delta_e", "value": de, "limit": r["max_delta_e"], "ok": ok}
                )
                if not ok:
                    violations.append(
                        {
                            "fiber": fiber,
                            "metric": "delta_e",
                            "value": de,
                            "limit": r["max_delta_e"],
                            "severity": severity,
                        }
                    )
                    if severity == "blocking":
                        fiber_pass = False
            if r.get("min_gray_scale_grade") is not None and grade is not None:
                any_rule_applied = True
                ok = grade >= r["min_gray_scale_grade"]
                checks.append(
                    {
                        "metric": "gray_scale_grade",
                        "value": grade,
                        "limit": r["min_gray_scale_grade"],
                        "ok": ok,
                    }
                )
                if not ok:
                    violations.append(
                        {
                            "fiber": fiber,
                            "metric": "gray_scale_grade",
                            "value": grade,
                            "limit": r["min_gray_scale_grade"],
                            "severity": severity,
                        }
                    )
                    if severity == "blocking":
                        fiber_pass = False
        per_fiber[fiber] = {"pass": fiber_pass, "checks": checks}

    overall = any_rule_applied and all(f["pass"] for f in per_fiber.values())
    return {
        "overall_pass": overall,
        "evaluated": any_rule_applied,
        "per_fiber": per_fiber,
        "violations": violations,
    }


# ── DB operations ───────────────────────────────────────────────────────────────
async def _resolve_method_id(session: AsyncSession, code: str | None) -> uuid.UUID | None:
    if not code:
        return None
    method = (
        await session.execute(select(TestMethod).where(TestMethod.code == code))
    ).scalar_one_or_none()
    if method is None:
        raise NotFoundError(f"Unknown test method code: {code}")
    return method.id


async def create_test_job(
    session: AsyncSession,
    company_id: uuid.UUID,
    requested_by: uuid.UUID,
    data: TestJobCreate,
) -> TestJob:
    method_id = await _resolve_method_id(session, data.test_method_code)
    job = TestJob(
        company_id=company_id,
        department_id=data.department_id,
        brand_specification_id=data.brand_specification_id,
        test_method_id=method_id,
        barcode=data.barcode,
        article_code=data.article_code,
        lot_code=data.lot_code,
        article_id=data.article_id,
        article_variant_id=data.article_variant_id,
        requested_by=requested_by,
        meta=data.metadata,
    )
    session.add(job)
    await session.flush()
    return job


async def list_test_jobs(
    session: AsyncSession,
    company_id: uuid.UUID,
    *,
    status: str | None = None,
    brand_specification_id: uuid.UUID | None = None,
) -> list[TestJob]:
    stmt = select(TestJob).where(TestJob.company_id == company_id)
    if status is not None:
        stmt = stmt.where(TestJob.status == status)
    if brand_specification_id is not None:
        stmt = stmt.where(TestJob.brand_specification_id == brand_specification_id)
    stmt = stmt.order_by(TestJob.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())


async def get_test_job(session: AsyncSession, company_id: uuid.UUID, job_id: uuid.UUID) -> TestJob:
    stmt = select(TestJob).where(TestJob.id == job_id, TestJob.company_id == company_id)
    job = (await session.execute(stmt)).scalar_one_or_none()
    if job is None:
        raise NotFoundError("Test job not found")
    return job


async def _load_rule_dicts(
    session: AsyncSession, company_id: uuid.UUID, spec_id: uuid.UUID
) -> list[dict]:
    stmt = select(BrandAcceptanceRule).where(
        BrandAcceptanceRule.company_id == company_id,
        BrandAcceptanceRule.brand_specification_id == spec_id,
        BrandAcceptanceRule.is_active.is_(True),
    )
    rules = (await session.execute(stmt)).scalars().all()
    return [
        {
            "test_method_code": r.test_method_code,
            "fiber_code": r.fiber_code,
            "max_delta_e": float(r.max_delta_e) if r.max_delta_e is not None else None,
            "min_gray_scale_grade": (
                float(r.min_gray_scale_grade) if r.min_gray_scale_grade is not None else None
            ),
            "severity": r.severity,
        }
        for r in rules
    ]


async def submit_manual_result(
    session: AsyncSession,
    company_id: uuid.UUID,
    job_id: uuid.UUID,
    data: ManualResultCreate,
) -> tuple[TestJob, MeasurementResult]:
    job = await get_test_job(session, company_id, job_id)

    rules: list[dict] = []
    if job.brand_specification_id is not None:
        rules = await _load_rule_dicts(session, company_id, job.brand_specification_id)

    fibers = {k: v.model_dump() for k, v in data.fibers.items()}
    verdict = evaluate_pass_fail(rules, data.test_method_code, fibers)

    result = MeasurementResult(
        company_id=company_id,
        test_job_id=job.id,
        algorithm_version=MANUAL_ALGO_VERSION,
        results={"test_method_code": data.test_method_code, "fibers": fibers, "notes": data.notes},
        pass_fail=verdict,
    )
    session.add(result)

    if not verdict["evaluated"]:
        job.status = "completed"
    else:
        job.status = "passed" if verdict["overall_pass"] else "failed"
    await session.flush()
    return job, result


async def get_results(
    session: AsyncSession, company_id: uuid.UUID, job_id: uuid.UUID
) -> list[MeasurementResult]:
    await get_test_job(session, company_id, job_id)  # tenant-scoped existence
    stmt = (
        select(MeasurementResult)
        .where(
            MeasurementResult.company_id == company_id,
            MeasurementResult.test_job_id == job_id,
        )
        .order_by(MeasurementResult.created_at.desc())
    )
    return list((await session.execute(stmt)).scalars().all())
