from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Device(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Registered capture device (iPhone). Calibration matrices are stored as
    JSONB per illuminant (D65 / TL84)."""

    __tablename__ = "devices"
    __table_args__ = (UniqueConstraint("company_id", "hardware_uuid", name="uq_device_company_hw"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    hardware_uuid: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str | None] = mapped_column(Text)
    os_version: Mapped[str | None] = mapped_column(Text)
    mdm_managed: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
    calibration_profile: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    active_d65_matrix: Mapped[dict | None] = mapped_column(JSONB)
    active_tl84_matrix: Mapped[dict | None] = mapped_column(JSONB)
