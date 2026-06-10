from __future__ import annotations

import csv
import io
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.brand_specs.schemas import AcceptanceRuleIn, BrandSpecCreate
from app.common.errors import AppError, ConflictError, NotFoundError
from app.db.models import BrandAcceptanceRule, BrandSpecification


def parse_rules_csv(text: str) -> list[AcceptanceRuleIn]:
    """Parse a capitolato rules table (CSV) into acceptance rules.

    Columns (positional): test_method_code, fiber_code, max_delta_e,
    min_gray_scale_grade, severity. Handles Italian Excel (';' delimiter and
    decimal comma) and an optional header row."""
    text = (text or "").strip()
    if not text:
        raise AppError("CSV vuoto.", code="empty_csv")
    first_line = text.splitlines()[0]
    delimiter = ";" if first_line.count(";") >= first_line.count(",") else ","
    rows = [
        r for r in csv.reader(io.StringIO(text), delimiter=delimiter) if any(c.strip() for c in r)
    ]
    if rows:
        head = rows[0][0].strip().lower()
        if "method" in head or "metodo" in head or "test" in head:
            rows = rows[1:]

    out: list[AcceptanceRuleIn] = []
    for idx, row in enumerate(rows, start=1):
        cells = [c.strip() for c in row]
        if not cells or not cells[0]:
            continue

        def num(i: int, _idx: int = idx, _cells: list[str] = cells) -> float | None:
            if i < len(_cells) and _cells[i]:
                try:
                    return float(_cells[i].replace(",", "."))
                except ValueError as exc:
                    raise AppError(
                        f"Riga {_idx}: numero non valido '{_cells[i]}'.", code="bad_csv"
                    ) from exc
            return None

        severity = cells[4].lower() if len(cells) > 4 and cells[4] else "blocking"
        if severity not in ("blocking", "warning"):
            severity = "blocking"
        out.append(
            AcceptanceRuleIn(
                test_method_code=cells[0],
                fiber_code=(cells[1] if len(cells) > 1 and cells[1] else None),
                max_delta_e=num(2),
                min_gray_scale_grade=num(3),
                severity=severity,
            )
        )
    if not out:
        raise AppError("Nessuna regola valida nel CSV.", code="empty_csv")
    return out


def _rule_model(
    company_id: uuid.UUID, spec_id: uuid.UUID, rule: AcceptanceRuleIn
) -> BrandAcceptanceRule:
    return BrandAcceptanceRule(
        company_id=company_id,
        brand_specification_id=spec_id,
        test_method_code=rule.test_method_code,
        fiber_code=rule.fiber_code,
        max_delta_e=Decimal(str(rule.max_delta_e)) if rule.max_delta_e is not None else None,
        min_gray_scale_grade=(
            Decimal(str(rule.min_gray_scale_grade))
            if rule.min_gray_scale_grade is not None
            else None
        ),
        severity=rule.severity,
        rule_payload=rule.rule_payload,
    )


async def create_brand_spec(
    session: AsyncSession, company_id: uuid.UUID, data: BrandSpecCreate
) -> BrandSpecification:
    spec = BrandSpecification(
        id=uuid.uuid4(),
        company_id=company_id,
        brand_name=data.brand_name,
        description=data.description,
        meta=data.metadata,
    )
    session.add(spec)
    try:
        async with session.begin_nested():
            await session.flush()
    except IntegrityError as exc:
        raise ConflictError("A brand specification with this name already exists") from exc

    for rule in data.rules:
        session.add(_rule_model(company_id, spec.id, rule))
    await session.flush()
    return spec


async def list_brand_specs(
    session: AsyncSession, company_id: uuid.UUID
) -> list[BrandSpecification]:
    stmt = (
        select(BrandSpecification)
        .where(BrandSpecification.company_id == company_id)
        .order_by(BrandSpecification.brand_name)
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_brand_spec(
    session: AsyncSession, company_id: uuid.UUID, spec_id: uuid.UUID
) -> BrandSpecification:
    stmt = select(BrandSpecification).where(
        BrandSpecification.id == spec_id, BrandSpecification.company_id == company_id
    )
    spec = (await session.execute(stmt)).scalar_one_or_none()
    if spec is None:
        raise NotFoundError("Brand specification not found")
    return spec


async def get_rules(
    session: AsyncSession, company_id: uuid.UUID, spec_id: uuid.UUID
) -> list[BrandAcceptanceRule]:
    stmt = select(BrandAcceptanceRule).where(
        BrandAcceptanceRule.company_id == company_id,
        BrandAcceptanceRule.brand_specification_id == spec_id,
    )
    return list((await session.execute(stmt)).scalars().all())


async def add_rule(
    session: AsyncSession, company_id: uuid.UUID, spec_id: uuid.UUID, rule: AcceptanceRuleIn
) -> BrandAcceptanceRule:
    await get_brand_spec(session, company_id, spec_id)  # ensure exists / tenant scoped
    model = _rule_model(company_id, spec_id, rule)
    session.add(model)
    await session.flush()
    return model
