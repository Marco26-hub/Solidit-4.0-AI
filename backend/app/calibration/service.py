from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calibration.schemas import CalibrationReferenceCreate
from app.common.errors import AppError, ConflictError, NotFoundError
from app.db.models import CalibrationReference

EXPIRING_DAYS = 30  # warn when a reference expires within this window


def today() -> dt.date:
    return dt.datetime.now(dt.UTC).date()


def compute_validity(ref: CalibrationReference, ref_date: dt.date | None = None) -> str:
    """valid | expiring | expired | retired (pure, testable)."""
    if ref.status == "retired":
        return "retired"
    d = ref_date or today()
    if ref.valid_until is not None:
        if ref.valid_until < d:
            return "expired"
        if (ref.valid_until - d).days <= EXPIRING_DAYS:
            return "expiring"
    if ref.valid_from is not None and ref.valid_from > d:
        return "expired"  # not yet in force -> treat as not usable
    return "valid"


def is_usable(ref: CalibrationReference, ref_date: dt.date | None = None) -> bool:
    return compute_validity(ref, ref_date) in ("valid", "expiring")


async def create_reference(
    session: AsyncSession, company_id: uuid.UUID, data: CalibrationReferenceCreate
) -> CalibrationReference:
    existing = (
        await session.execute(
            select(CalibrationReference).where(
                CalibrationReference.company_id == company_id,
                CalibrationReference.kind == data.kind,
                CalibrationReference.code == data.code,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError(f"Reference {data.kind}/{data.code} already exists")
    ref = CalibrationReference(
        company_id=company_id,
        kind=data.kind,
        code=data.code,
        description=data.description,
        certificate_number=data.certificate_number,
        valid_from=data.valid_from,
        valid_until=data.valid_until,
    )
    session.add(ref)
    await session.flush()
    return ref


async def list_references(
    session: AsyncSession, company_id: uuid.UUID
) -> list[CalibrationReference]:
    return list(
        (
            await session.execute(
                select(CalibrationReference)
                .where(CalibrationReference.company_id == company_id)
                .order_by(CalibrationReference.kind, CalibrationReference.code)
            )
        )
        .scalars()
        .all()
    )


async def get_reference(
    session: AsyncSession, company_id: uuid.UUID, ref_id: uuid.UUID
) -> CalibrationReference:
    ref = (
        await session.execute(
            select(CalibrationReference).where(
                CalibrationReference.id == ref_id,
                CalibrationReference.company_id == company_id,
            )
        )
    ).scalar_one_or_none()
    if ref is None:
        raise NotFoundError("Calibration reference not found")
    return ref


async def retire_reference(
    session: AsyncSession, company_id: uuid.UUID, ref_id: uuid.UUID
) -> CalibrationReference:
    ref = await get_reference(session, company_id, ref_id)
    ref.status = "retired"
    await session.flush()
    return ref


async def assert_capture_references_valid(
    session: AsyncSession,
    company_id: uuid.UUID,
    ref_ids: dict[str, uuid.UUID | None],
) -> dict[str, dict]:
    """Validate the references linked to a capture. Raise AppError if any is
    expired/retired (ISO 17025: cannot analyse with an out-of-date reference).
    Returns a provenance dict {slot: {id, kind, code, validity}} for usable ones.
    Slots with no reference are simply omitted (soft — flagged as a warning)."""
    provenance: dict[str, dict] = {}
    blocked: list[str] = []
    for slot, rid in ref_ids.items():
        if rid is None:
            continue
        ref = await get_reference(session, company_id, rid)
        v = compute_validity(ref)
        if v in ("expired", "retired"):
            blocked.append(f"{slot}={ref.code} ({v})")
        provenance[slot] = {
            "id": str(ref.id),
            "kind": ref.kind,
            "code": ref.code,
            "validity": v,
        }
    if blocked:
        raise AppError(
            "Riferimenti non validi (scaduti/dismessi): " + "; ".join(blocked),
            code="reference_invalid",
        )
    return provenance
