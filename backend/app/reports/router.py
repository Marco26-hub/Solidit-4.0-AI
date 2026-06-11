from __future__ import annotations

import io
import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_tenant_principal, require_role
from app.reports import service
from app.reports.schemas import ReportOut, ReportVerify

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

_FINALIZE = require_role("company_admin", "lab_manager")


@router.get("", response_model=list[ReportOut])
async def certificate_ledger(
    status_filter: str | None = Query(default=None, alias="status"),
    test_job_id: uuid.UUID | None = Query(default=None),
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[ReportOut]:
    rows = await service.list_reports(
        session, principal.company_id, status=status_filter, test_job_id=test_job_id
    )
    return [ReportOut.model_validate(r) for r in rows]


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: uuid.UUID,
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> ReportOut:
    report = await service.get_report(session, principal.company_id, report_id)
    return ReportOut.model_validate(report)


@router.post("/{report_id}/finalize", response_model=ReportOut)
async def finalize_report(
    report_id: uuid.UUID,
    principal: Principal = Depends(_FINALIZE),
    session: AsyncSession = Depends(get_db),
) -> ReportOut:
    report = await service.finalize_report(session, principal.company_id, report_id)
    await record_audit(
        session,
        action="report.finalize",
        entity_type="quality_report",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=report.id,
        payload={"report_number": report.report_number},
    )
    return ReportOut.model_validate(report)


@router.get("/{report_id}/verify", response_model=ReportVerify)
async def verify_report(
    report_id: uuid.UUID,
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> ReportVerify:
    return ReportVerify(**await service.verify_report(session, principal.company_id, report_id))


@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    data, filename = await service.get_pdf(session, principal.company_id, report_id)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
