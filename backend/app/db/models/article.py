from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin


class Article(UUIDPrimaryKeyMixin, CreatedAtMixin, SoftDeleteMixin, Base):
    """Production article (the dyehouse/printer sample). The comparison
    reference for colour-change is per-VARIANT (colorway/lot)."""

    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_article_company_code"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str | None] = mapped_column(Text)
    composition: Mapped[str | None] = mapped_column(Text)  # e.g. "95% CO 5% EA"
    brand_specification_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("brand_specifications.id")
    )
    meta: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )


class ArticleVariant(UUIDPrimaryKeyMixin, CreatedAtMixin, SoftDeleteMixin, Base):
    """A colorway/lot of an article. Holds the production-sample reference
    colour (Lab) used for colour-change comparison."""

    __tablename__ = "article_variants"
    __table_args__ = (
        UniqueConstraint("company_id", "article_id", "code", name="uq_variant_article_code"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)  # colorway/variant code
    color_name: Mapped[str | None] = mapped_column(Text)
    lot_code: Mapped[str | None] = mapped_column(Text)
    # reference Lab of the untreated production sample {"L":..,"a":..,"b":..}
    reference_lab: Mapped[dict | None] = mapped_column(JSONB)
    meta: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )


class GradingProfile(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Configurable ΔE→grade mapping per norm family and assessment type.

    company_id NULL = builtin EXAMPLE profile (seeded by migration; thresholds
    are NON-proprietary placeholders to be replaced by validated/licensed
    values). Tenant rows override builtins with the same family+type."""

    __tablename__ = "grading_profiles"

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    standard_family: Mapped[str] = mapped_column(Text, nullable=False)  # ISO_105|AATCC|ASTM
    assessment_type: Mapped[str] = mapped_column(Text, nullable=False)  # staining|change
    thresholds: Mapped[list] = mapped_column(JSONB, nullable=False)
    is_builtin: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
