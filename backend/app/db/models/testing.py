from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class TestMethod(UUIDPrimaryKeyMixin, Base):
    """Global reference table (no tenant, no RLS). Seeded by migration 0002."""

    __tablename__ = "test_methods"

    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    standard_family: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )


class TestJob(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "test_jobs"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("departments.id")
    )
    brand_specification_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("brand_specifications.id")
    )
    test_method_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("test_methods.id")
    )
    barcode: Mapped[str | None] = mapped_column(Text)
    article_code: Mapped[str | None] = mapped_column(Text)
    lot_code: Mapped[str | None] = mapped_column(Text)
    # production-sample reference (article + colorway variant), migration 0006
    article_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("articles.id")
    )
    article_variant_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("article_variants.id")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="created")
    requested_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id")
    )
    meta: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )


class MeasurementResult(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "measurement_results"

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
    # FK to capture_sessions is enforced in the DB (migration 0001); no ORM model
    # for capture_sessions yet (Sprint 3 / Vision), so keep this column FK-free here.
    capture_session_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    algorithm_version: Mapped[str] = mapped_column(Text, nullable=False)
    results: Mapped[dict] = mapped_column(JSONB, nullable=False)
    pass_fail: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
