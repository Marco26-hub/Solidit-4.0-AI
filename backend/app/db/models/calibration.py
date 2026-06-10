from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import Date, ForeignKey, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# physical reference kinds tracked for validity/expiry
REFERENCE_KINDS = ("grey_scale", "white_tile", "colour_target", "lightbox", "other")


class CalibrationReference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A company's physical reference/instrument with certificate + validity:
    ISO grey scale, white tile, colour target, or lightbox. Analysis is blocked
    when a linked reference is expired or retired (ISO/IEC 17025 logic)."""

    __tablename__ = "calibration_references"
    __table_args__ = (
        UniqueConstraint("company_id", "kind", "code", name="uq_calref_company_kind_code"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    certificate_number: Mapped[str | None] = mapped_column(Text)
    valid_from: Mapped[dt.date | None] = mapped_column(Date)
    valid_until: Mapped[dt.date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="active")
    meta: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
