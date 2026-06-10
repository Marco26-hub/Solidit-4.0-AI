from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_principal, get_tenant_principal, require_role
from app.common.errors import NotFoundError
from app.common.storage import get_storage
from app.db.models import TestMethod
from app.test_methods import service

router = APIRouter(prefix="/api/v1/test-methods", tags=["test-methods"])

_MANAGE = require_role("company_admin", "lab_manager")


class TestMethodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: object
    code: str
    name: str
    category: str
    standard_family: str | None
    metadata: dict = {}


class MethodDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test_method_code: str
    filename: str
    sha256_hash: str
    content_type: str | None


@router.get("", response_model=list[TestMethodOut])
async def list_test_methods(
    _: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> list[TestMethodOut]:
    rows = (await session.execute(select(TestMethod).order_by(TestMethod.code))).scalars().all()
    return [
        TestMethodOut(
            id=m.id,
            code=m.code,
            name=m.name,
            category=m.category,
            standard_family=m.standard_family,
            metadata=m.meta,
        )
        for m in rows
    ]


@router.get("/documents", response_model=list[MethodDocumentOut])
async def list_method_documents(
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[MethodDocumentOut]:
    docs = await service.list_documents(session, principal.company_id)
    return [MethodDocumentOut.model_validate(d) for d in docs]


@router.post(
    "/{code}/document", response_model=MethodDocumentOut, status_code=status.HTTP_201_CREATED
)
async def upload_method_document(
    code: str,
    file: UploadFile = File(...),
    principal: Principal = Depends(_MANAGE),
    session: AsyncSession = Depends(get_db),
) -> MethodDocumentOut:
    """Attach the company's OWN licensed copy of the reference standard (PDF)."""
    data = await file.read()
    doc = await service.upload_document(
        session,
        principal.company_id,
        code,
        data,
        file.filename or f"{code}.pdf",
        file.content_type,
    )
    await record_audit(
        session,
        action="method.document_upload",
        entity_type="method_document",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=doc.id,
        payload={"method": code, "sha256": doc.sha256_hash},
    )
    return MethodDocumentOut.model_validate(doc)


@router.get("/{code}/document")
async def download_method_document(
    code: str,
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    doc = await service.get_document(session, principal.company_id, code)
    if doc is None:
        raise NotFoundError("Nessuna norma di riferimento caricata per questo metodo.")
    data = get_storage().get(doc.storage_key)
    from io import BytesIO

    return StreamingResponse(
        BytesIO(data),
        media_type=doc.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.filename}"'},
    )
