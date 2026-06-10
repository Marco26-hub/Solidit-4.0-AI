from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class QualityReport(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "quality_reports"
    __table_args__ = (
        UniqueConstraint("company_id", "report_number", name="uq_report_company_number"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_job_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("test_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_number: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_storage_key: Mapped[str | None] = mapped_column(Text)
    report_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # SHA-256 cryptographic integrity seal (NOT a qualified digital signature)
    sha256_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="generated")


class ReportSignature(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "report_signatures"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quality_report_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("quality_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id")
    )
    signature_type: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="integrity_seal"
    )
    sha256_hash: Mapped[str] = mapped_column(Text, nullable=False)
    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    meta: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
