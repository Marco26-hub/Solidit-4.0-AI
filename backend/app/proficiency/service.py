from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ProficiencyTest
from app.proficiency.schemas import ProficiencyTestCreate


def evaluate(
    x: float,
    assigned: float,
    sigma: float | None,
    u_lab: float | None = None,
    u_ref: float | None = None,
) -> tuple[float | None, float | None, str]:
    """Compute (z_score, En, verdict).

    z = (x - X) / sigma  → |z|≤2 soddisfacente, 2<|z|<3 discutibile, ≥3 non soddisfacente.
    En = (x - X) / sqrt(U_lab² + U_ref²)  → |En|≤1 soddisfacente (bilateral ILC).
    The z-score drives the verdict when sigma is given; otherwise En; else n/d.
    """
    z = round((x - assigned) / sigma, 3) if sigma else None
    en = None
    if u_lab is not None and u_ref is not None:
        den = (u_lab**2 + u_ref**2) ** 0.5
        en = round((x - assigned) / den, 3) if den else None

    if z is not None:
        az = abs(z)
        verdict = "soddisfacente" if az <= 2 else ("discutibile" if az < 3 else "non soddisfacente")
    elif en is not None:
        verdict = "soddisfacente" if abs(en) <= 1 else "non soddisfacente"
    else:
        verdict = "n/d"
    return z, en, verdict


async def create(
    session: AsyncSession, company_id: uuid.UUID, data: ProficiencyTestCreate
) -> ProficiencyTest:
    z, en, verdict = evaluate(
        data.result_x, data.assigned_value, data.std_dev, data.u_lab, data.u_ref
    )
    pt = ProficiencyTest(
        company_id=company_id,
        scheme=data.scheme,
        round_label=data.round_label,
        parameter=data.parameter,
        test_method_code=data.test_method_code,
        result_x=data.result_x,
        assigned_value=data.assigned_value,
        std_dev=data.std_dev,
        u_lab=data.u_lab,
        u_ref=data.u_ref,
        z_score=z,
        en_number=en,
        verdict=verdict,
        test_date=data.test_date,
    )
    session.add(pt)
    await session.flush()
    return pt


async def list_all(session: AsyncSession, company_id: uuid.UUID) -> list[ProficiencyTest]:
    return list(
        (
            await session.execute(
                select(ProficiencyTest)
                .where(ProficiencyTest.company_id == company_id)
                .order_by(ProficiencyTest.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
