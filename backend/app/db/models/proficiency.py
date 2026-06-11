from __future__ import annotations

import datetime as dt
import decimal
import uuid

from sqlalchemy import Date, ForeignKey, Numeric, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class ProficiencyTest(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """An inter-laboratory comparison / proficiency-testing round result and its
    evaluation (z-score, En number, verdict). The external scheme is run by an
    accredited PT provider; this records the lab's performance (ISO 17025 7.7.2)."""

    __tablename__ = "proficiency_tests"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scheme: Mapped[str] = mapped_column(Text, nullable=False)
    round_label: Mapped[str] = mapped_column(Text, nullable=False)
    parameter: Mapped[str | None] = mapped_column(Text)
    test_method_code: Mapped[str | None] = mapped_column(Text)
    result_x: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    assigned_value: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    std_dev: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 4))
    u_lab: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 4))
    u_ref: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 4))
    z_score: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 3))
    en_number: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 3))
    verdict: Mapped[str] = mapped_column(Text, nullable=False, server_default="n/d")
    test_date: Mapped[dt.date | None] = mapped_column(Date)
    meta: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
