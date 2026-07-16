from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_tenant_principal, require_role
from app.reports import service as reports_service
from app.reports.schemas import ReportOut
from app.test_jobs import service
from app.test_jobs.schemas import (
    ManualResultCreate,
    MeasurementResultOut,
    TestJobCreate,
    TestJobOut,
)

router = APIRouter(prefix="/api/v1/test-jobs", tags=["test-jobs"])

# operators can run tests + enter results; managers/admins too
_OPERATE = require_role("company_admin", "lab_manager", "operator")
# report generation/approval is restricted to managers/admins
_REPORT_ROLES = require_role("company_admin", "lab_manager")


@router.get("", response_model=list[TestJobOut])
async def list_jobs(
    status_filter: str | None = Query(default=None, alias="status"),
    brand_specification_id: uuid.UUID | None = Query(default=None),
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[TestJobOut]:
    rows = await service.list_test_jobs(
        session,
        principal.company_id,
        status=status_filter,
        brand_specification_id=brand_specification_id,
    )
    return [TestJobOut.model_validate(j) for j in rows]


@router.post("", response_model=TestJobOut, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: TestJobCreate,
    principal: Principal = Depends(_OPERATE),
    session: AsyncSession = Depends(get_db),
) -> TestJobOut:
    job = await service.create_test_job(session, principal.company_id, principal.user_id, payload)
    await record_audit(
        session,
        action="test_job.create",
        entity_type="test_job",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=job.id,
        payload={"article_code": job.article_code, "lot_code": job.lot_code},
    )
    return TestJobOut.model_validate(job)


@router.get("/{job_id}", response_model=TestJobOut)
async def get_job(
    job_id: uuid.UUID,
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> TestJobOut:
    job = await service.get_test_job(session, principal.company_id, job_id)
    return TestJobOut.model_validate(job)


@router.post(
    "/{job_id}/manual-result",
    response_model=MeasurementResultOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_manual_result(
    job_id: uuid.UUID,
    payload: ManualResultCreate,
    principal: Principal = Depends(_OPERATE),
    session: AsyncSession = Depends(get_db),
) -> MeasurementResultOut:
    job, result = await service.submit_manual_result(
        session, principal.company_id, job_id, payload, operator_user_id=principal.user_id
    )
    await record_audit(
        session,
        action="test_job.manual_result",
        entity_type="measurement_result",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=result.id,
        payload={"job_status": job.status, "overall_pass": result.pass_fail.get("overall_pass")},
    )
    return MeasurementResultOut.model_validate(result)


@router.get("/{job_id}/results", response_model=list[MeasurementResultOut])
async def get_results(
    job_id: uuid.UUID,
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[MeasurementResultOut]:
    rows = await service.get_results(session, principal.company_id, job_id)
    return [MeasurementResultOut.model_validate(r) for r in rows]


@router.post("/{job_id}/reports", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def generate_report(
    job_id: uuid.UUID,
    principal: Principal = Depends(_REPORT_ROLES),
    session: AsyncSession = Depends(get_db),
) -> ReportOut:
    report = await reports_service.generate_report(
        session, principal.company_id, principal.user_id, job_id
    )
    await record_audit(
        session,
        action="report.generate",
        entity_type="quality_report",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=report.id,
        payload={"report_number": report.report_number, "sha256": report.sha256_hash},
    )
    return ReportOut.model_validate(report)
