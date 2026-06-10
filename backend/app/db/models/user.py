from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Global identity. NOT tenant-scoped: a user may belong to many companies
    via ``CompanyMembership``. No RLS on this table."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
