from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError, NotFoundError
from app.common.storage import get_storage
from app.config import settings
from app.db.models import (
    BrandSpecification,
    Company,
    MeasurementResult,
    QualityReport,
    ReportSignature,
)
from app.reports.pdf import build_report_pdf
from app.test_jobs.service import get_test_job


def canonical_hash(payload: dict) -> str:
    """Deterministic SHA-256 over the report payload (key-order independent)."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


async def _latest_result(
    session: AsyncSession, company_id: uuid.UUID, job_id: uuid.UUID
) -> MeasurementResult | None:
    stmt = (
        select(MeasurementResult)
        .where(
            MeasurementResult.company_id == company_id,
            MeasurementResult.test_job_id == job_id,
        )
        .order_by(MeasurementResult.created_at.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def generate_report(
    session: AsyncSession,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
) -> QualityReport:
    job = await get_test_job(session, company_id, job_id)
    result = await _latest_result(session, company_id, job_id)
    if result is None:
        raise AppError(
            "Cannot generate a report: the test job has no measurement result yet.",
            code="no_result",
        )

    company = (await session.execute(select(Company).where(Company.id == company_id))).scalar_one()

    brand = None
    if job.brand_specification_id is not None:
        spec = (
            await session.execute(
                select(BrandSpecification).where(
                    BrandSpecification.id == job.brand_specification_id
                )
            )
        ).scalar_one_or_none()
        if spec is not None:
            brand = {"id": str(spec.id), "name": spec.brand_name}

    report_id = uuid.uuid4()
    now = datetime.now(UTC)
    report_number = f"RPT-{now.year}-{report_id.hex[:8].upper()}"

    payload = {
        "report_number": report_number,
        "company": {"id": str(company.id), "name": company.name},
        "test_job": {
            "id": str(job.id),
            "article_code": job.article_code,
            "lot_code": job.lot_code,
            "barcode": job.barcode,
            "status": job.status,
        },
        "test_method_code": result.results.get("test_method_code"),
        "brand": brand,
        "measurement": {
            "algorithm_version": result.algorithm_version,
            "results": result.results,
            "pass_fail": result.pass_fail,
        },
        "generated_at": now.isoformat(),
        "generated_by": str(user_id),
    }

    sha = canonical_hash(payload)
    verify_url = f"{settings.public_base_url}/api/v1/reports/{report_id}/verify"
    pdf_bytes = build_report_pdf(payload, sha, verify_url)

    storage_key = f"reports/{company_id}/{report_id}.pdf"
    get_storage().put(storage_key, pdf_bytes, "application/pdf")

    report = QualityReport(
        id=report_id,
        company_id=company_id,
        test_job_id=job.id,
        report_number=report_number,
        pdf_storage_key=storage_key,
        report_payload=payload,
        sha256_hash=sha,
        status="generated",
    )
    session.add(report)
    session.add(
        ReportSignature(
            company_id=company_id,
            quality_report_id=report_id,
            signer_user_id=user_id,
            signature_type="integrity_seal",
            sha256_hash=sha,
        )
    )
    await session.flush()
    return report


async def list_reports(
    session: AsyncSession,
    company_id: uuid.UUID,
    *,
    status: str | None = None,
    test_job_id: uuid.UUID | None = None,
) -> list[QualityReport]:
    stmt = select(QualityReport).where(QualityReport.company_id == company_id)
    if status is not None:
        stmt = stmt.where(QualityReport.status == status)
    if test_job_id is not None:
        stmt = stmt.where(QualityReport.test_job_id == test_job_id)
    stmt = stmt.order_by(QualityReport.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())


async def get_report(
    session: AsyncSession, company_id: uuid.UUID, report_id: uuid.UUID
) -> QualityReport:
    stmt = select(QualityReport).where(
        QualityReport.id == report_id, QualityReport.company_id == company_id
    )
    report = (await session.execute(stmt)).scalar_one_or_none()
    if report is None:
        raise NotFoundError("Report not found")
    return report


async def verify_report(session: AsyncSession, company_id: uuid.UUID, report_id: uuid.UUID) -> dict:
    report = await get_report(session, company_id, report_id)
    recomputed = canonical_hash(report.report_payload)
    return {
        "report_number": report.report_number,
        "sha256_hash": report.sha256_hash,
        "recomputed_hash": recomputed,
        "valid": recomputed == report.sha256_hash,
    }


async def get_pdf(
    session: AsyncSession, company_id: uuid.UUID, report_id: uuid.UUID
) -> tuple[bytes, str]:
    report = await get_report(session, company_id, report_id)
    if not report.pdf_storage_key:
        raise NotFoundError("Report PDF not available")
    data = get_storage().get(report.pdf_storage_key)
    return data, f"{report.report_number}.pdf"
