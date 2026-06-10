from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError, NotFoundError
from app.common.storage import get_storage
from app.db.models import MethodDocument, TestMethod


async def _ensure_method(session: AsyncSession, code: str) -> TestMethod:
    method = (
        await session.execute(select(TestMethod).where(TestMethod.code == code))
    ).scalar_one_or_none()
    if method is None:
        raise NotFoundError(f"Unknown test method code: {code}")
    return method


async def get_document(
    session: AsyncSession, company_id: uuid.UUID, code: str
) -> MethodDocument | None:
    return (
        await session.execute(
            select(MethodDocument).where(
                MethodDocument.company_id == company_id,
                MethodDocument.test_method_code == code,
            )
        )
    ).scalar_one_or_none()


async def upload_document(
    session: AsyncSession,
    company_id: uuid.UUID,
    code: str,
    data: bytes,
    filename: str,
    content_type: str | None,
) -> MethodDocument:
    """Store the company's OWN licensed copy of the reference norm for a method.
    Upserts: re-uploading replaces the existing copy for that method."""
    await _ensure_method(session, code)
    if not data:
        raise AppError("File vuoto.", code="empty_file")
    sha = hashlib.sha256(data).hexdigest()
    key = f"norms/{company_id}/{code}/{uuid.uuid4().hex}-{filename}"
    get_storage().put(key, data, content_type or "application/octet-stream")

    doc = await get_document(session, company_id, code)
    if doc is None:
        doc = MethodDocument(
            company_id=company_id,
            test_method_code=code,
            filename=filename,
            storage_key=key,
            sha256_hash=sha,
            content_type=content_type,
        )
        session.add(doc)
    else:
        doc.filename = filename
        doc.storage_key = key
        doc.sha256_hash = sha
        doc.content_type = content_type
    await session.flush()
    return doc


async def list_documents(session: AsyncSession, company_id: uuid.UUID) -> list[MethodDocument]:
    return list(
        (
            await session.execute(
                select(MethodDocument)
                .where(MethodDocument.company_id == company_id)
                .order_by(MethodDocument.test_method_code)
            )
        )
        .scalars()
        .all()
    )
