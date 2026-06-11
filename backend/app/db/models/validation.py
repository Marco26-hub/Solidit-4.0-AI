from __future__ import annotations

import decimal
import uuid

from sqlalchemy import ForeignKey, Numeric, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class ValidationRun(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """A method-validation campaign. `dataset_ref` is the campaign name;
    computed statistics live in `metrics` (software vs reference)."""

    __tablename__ = "validation_runs"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    dataset_ref: Mapped[str | None] = mapped_column(Text)
    metrics: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending")


class ValidationSample(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One validation point: the software grade vs a reference grade (from a
    spectrophotometer, expert visual assessment, or an external lab)."""

    __tablename__ = "validation_samples"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    validation_run_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("validation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sample_code: Mapped[str] = mapped_column(Text, nullable=False)
    fiber: Mapped[str | None] = mapped_column(Text)
    reference_method: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="spectrophotometer"
    )
    software_grade: Mapped[decimal.Decimal | None] = mapped_column(Numeric(3, 1))
    reference_grade: Mapped[decimal.Decimal | None] = mapped_column(Numeric(3, 1))
    software_delta_e: Mapped[decimal.Decimal | None] = mapped_column(Numeric(8, 3))
    reference_delta_e: Mapped[decimal.Decimal | None] = mapped_column(Numeric(8, 3))
    meta: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
