from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError, ConflictError, NotFoundError
from app.common.storage import get_storage
from app.config import settings
from app.db.models import (
    BrandSpecification,
    Company,
    MeasurementResult,
    QualityReport,
    ReportSignature,
    ReportVerification,
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

    # a locked report is the official emission — do not silently emit another
    existing = await list_reports(session, company_id, test_job_id=job_id)
    locked = next((r for r in existing if r.status == "locked"), None)
    if locked is not None:
        raise ConflictError(
            f"Esiste già un report bloccato per questa prova ({locked.report_number}).",
            code="report_locked",
        )

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

    # explicit provenance for the report (accreditation: nothing hidden)
    res = result.results or {}
    vision = res.get("vision", {}) if isinstance(res, dict) else {}
    qflags = vision.get("quality_flags", {}) if isinstance(vision, dict) else {}
    # ISO 17025 §6.2: the operator who produced the result, with authorisation status
    operator_info = res.get("operator") if isinstance(res, dict) else None
    operator_email = None
    if result.operator_user_id is not None:
        from app.db.models import User

        u = (
            await session.execute(select(User).where(User.id == result.operator_user_id))
        ).scalar_one_or_none()
        operator_email = u.email if u else None

    provenance = {
        "algorithm_version": result.algorithm_version,
        "operator_email": operator_email,
        "operator_authorized": (operator_info or {}).get("authorized"),
        "source": res.get("source", "manual"),
        "assessment_type": res.get("assessment_type"),
        "references": res.get("references", {}),
        "grading_profile": qflags.get("grading_profile"),
        "colour_correction": qflags.get("colour_correction"),
        "geometry": (qflags.get("geometry") or {}).get("method"),
        "grey_scale_detected": (qflags.get("grey_scale") or {}).get("detected"),
        "fiber_order": qflags.get("fiber_order"),
        "capture_acceptable": (qflags.get("capture") or {}).get("acceptable"),
        "repeatability": vision.get("repeatability"),
        "warnings": vision.get("warnings", []),
    }

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
        "test_method_code": res.get("test_method_code") if isinstance(res, dict) else None,
        "brand": brand,
        "measurement": {
            "algorithm_version": result.algorithm_version,
            "results": result.results,
            "pass_fail": result.pass_fail,
        },
        "provenance": provenance,
        "generated_at": now.isoformat(),
        "generated_by": str(user_id),
    }

    sha = canonical_hash(payload)
    # QR points to the PUBLIC verification page (anyone can check authenticity)
    verify_url = f"{settings.web_base_url}/verify/{report_id}?h={sha}"
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
    # public verification mirror (non-sensitive fields, readable without auth)
    session.add(
        ReportVerification(
            report_id=report_id,
            company_id=company_id,
            report_number=report_number,
            sha256_hash=sha,
            company_name=company.name,
        )
    )
    await session.flush()
    return report


async def finalize_report(
    session: AsyncSession, company_id: uuid.UUID, report_id: uuid.UUID
) -> QualityReport:
    """Lock a report as the official emission. Immutable afterwards; idempotent."""
    report = await get_report(session, company_id, report_id)
    if report.status == "locked":
        return report
    report.status = "locked"
    report.locked_at = datetime.now(UTC)
    ver = (
        await session.execute(
            select(ReportVerification).where(ReportVerification.report_id == report_id)
        )
    ).scalar_one_or_none()
    if ver is not None:
        ver.locked = True
    await session.flush()
    return report


async def public_verify(session: AsyncSession, report_id: uuid.UUID, given_hash: str) -> dict:
    """Unauthenticated verification: confirm a report's integrity from the QR.
    Returns non-sensitive fields only. valid=True iff the report exists AND the
    supplied hash matches the stored seal (so ids alone can't be enumerated)."""
    ver = (
        await session.execute(
            select(ReportVerification).where(ReportVerification.report_id == report_id)
        )
    ).scalar_one_or_none()
    if ver is None or not given_hash or given_hash.lower() != ver.sha256_hash.lower():
        return {"valid": False}
    return {
        "valid": True,
        "report_number": ver.report_number,
        "company_name": ver.company_name,
        "issued_at": ver.issued_at.isoformat(),
        "locked": ver.locked,
        "sha256_hash": ver.sha256_hash,
    }


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
