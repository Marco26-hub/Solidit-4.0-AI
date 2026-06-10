from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class RefreshToken(UUIDPrimaryKeyMixin, Base):
    """Server-side refresh-token state for rotation + reuse detection.

    Global (per-user), no RLS. A 'family' is a chain of rotated tokens from one
    login; presenting an already-used/revoked jti is treated as theft and the
    whole family is revoked."""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    jti: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False)
    family_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_jti: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
