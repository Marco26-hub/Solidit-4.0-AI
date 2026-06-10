from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class CaptureSession(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "capture_sessions"

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
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("devices.id")
    )
    operator_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id")
    )
    # the multifiber lot used + which solidità this capture is for (added in 0005)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("multifiber_batches.id")
    )
    test_method_code: Mapped[str | None] = mapped_column(Text)
    # physical references/instruments used in this capture (migration 0008) —
    # analysis is blocked if a linked reference is expired/retired
    lightbox_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("calibration_references.id")
    )
    grey_scale_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("calibration_references.id")
    )
    white_tile_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("calibration_references.id")
    )
    colour_target_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("calibration_references.id")
    )
    capture_type: Mapped[str] = mapped_column(Text, nullable=False)
    illuminant: Mapped[str | None] = mapped_column(Text)
    telemetry: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    validation_status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending")
    validation_errors: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )


class ImageAsset(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "image_assets"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    capture_session_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("capture_sessions.id", ondelete="CASCADE"), index=True
    )
    asset_type: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(Text, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    meta: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
