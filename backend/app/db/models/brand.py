from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class BrandSpecification(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "brand_specifications"
    __table_args__ = (
        UniqueConstraint("company_id", "brand_name", name="uq_brand_spec_company_name"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    brand_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )


class BrandAcceptanceRule(UUIDPrimaryKeyMixin, CreatedAtMixin, SoftDeleteMixin, Base):
    __tablename__ = "brand_acceptance_rules"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    brand_specification_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("brand_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_method_code: Mapped[str] = mapped_column(Text, nullable=False)
    fiber_code: Mapped[str | None] = mapped_column(Text)
    max_delta_e: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    min_gray_scale_grade: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    rule_payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    severity: Mapped[str] = mapped_column(Text, nullable=False, server_default="blocking")
