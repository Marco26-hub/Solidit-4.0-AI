from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class MultifiberBatch(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Batch zero: the reference multifiber strip with lab Lab-values per fiber."""

    __tablename__ = "multifiber_batches"
    __table_args__ = (UniqueConstraint("company_id", "batch_code", name="uq_batch_company_code"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_code: Mapped[str] = mapped_column(Text, nullable=False)
    supplier: Mapped[str | None] = mapped_column(Text)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reference_lab_values: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="active")
    # which multifiber strip standard this batch uses (AATCC / ISO 105-F10 DW/TV …)
    strip_profile_code: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id")
    )
