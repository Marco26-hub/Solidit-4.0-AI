from __future__ import annotations

from sqlalchemy import Boolean, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class MultifiberStripProfile(UUIDPrimaryKeyMixin, Base):
    """Configurable multifiber strip composition (global reference, no RLS).

    Strips DIFFER by standard: AATCC vs ISO/UNI EN ISO 105-F10 (DW/TV) use
    different fibre types/order. ``fibers`` is the ORDERED list of fibre codes
    on the strip; batch-zero reference Lab values and vision ROIs follow it.
    Seeded with common types (migration 0004) — labs may edit/add profiles."""

    __tablename__ = "multifiber_strip_profiles"

    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    standard_family: Mapped[str | None] = mapped_column(Text)
    fibers: Mapped[list] = mapped_column(JSONB, nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
