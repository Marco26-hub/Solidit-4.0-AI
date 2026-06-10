from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class MethodDocument(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """A company's OWN licensed copy of a reference standard (ISO/UNI/AATCC PDF),
    attached to a test method code. Tenant-scoped — we never redistribute the
    copyrighted norm; each company uploads the copy it is licensed to hold."""

    __tablename__ = "method_documents"
    __table_args__ = (UniqueConstraint("company_id", "test_method_code", name="uq_method_doc"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_method_code: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str | None] = mapped_column(Text)
