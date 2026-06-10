from __future__ import annotations

import hashlib
import io
import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.brand_specs import service
from app.brand_specs.schemas import (
    AcceptanceRuleIn,
    AcceptanceRuleOut,
    BrandSpecCreate,
    BrandSpecImport,
    BrandSpecOut,
)
from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_tenant_principal, require_role
from app.common.errors import AppError, NotFoundError
from app.common.storage import get_storage
from app.db.models import BrandAcceptanceRule, BrandSpecification

_MAX_DOC_BYTES = 10 * 1024 * 1024

router = APIRouter(prefix="/api/v1/brand-specifications", tags=["brand-specs"])

_WRITE_ROLES = require_role("company_admin", "lab_manager")


def _to_out(spec: BrandSpecification, rules: list[BrandAcceptanceRule]) -> BrandSpecOut:
    out = BrandSpecOut.model_validate(spec)
    out.rules = [AcceptanceRuleOut.model_validate(r) for r in rules]
    return out


@router.get("", response_model=list[BrandSpecOut])
async def list_specs(
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[BrandSpecOut]:
    specs = await service.list_brand_specs(session, principal.company_id)
    rules = (
        (
            await session.execute(
                select(BrandAcceptanceRule).where(
                    BrandAcceptanceRule.company_id == principal.company_id
                )
            )
        )
        .scalars()
        .all()
    )
    by_spec: dict[uuid.UUID, list[BrandAcceptanceRule]] = {}
    for r in rules:
        by_spec.setdefault(r.brand_specification_id, []).append(r)
    return [_to_out(s, by_spec.get(s.id, [])) for s in specs]


@router.post("/import", response_model=BrandSpecOut, status_code=status.HTTP_201_CREATED)
async def import_spec(
    payload: BrandSpecImport,
    principal: Principal = Depends(_WRITE_ROLES),
    session: AsyncSession = Depends(get_db),
) -> BrandSpecOut:
    """Create a brand spec from a pasted capitolato CSV (test_method, fiber,
    max ΔE, min grey, severity)."""
    rules = service.parse_rules_csv(payload.rules_csv)
    spec = await service.create_brand_spec(
        session,
        principal.company_id,
        BrandSpecCreate(
            brand_name=payload.brand_name, description=payload.description, rules=rules
        ),
    )
    loaded = await service.get_rules(session, principal.company_id, spec.id)
    await record_audit(
        session,
        action="brand_spec.import",
        entity_type="brand_specification",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=spec.id,
        payload={"brand_name": spec.brand_name, "rules": len(loaded)},
    )
    return _to_out(spec, loaded)


@router.post("", response_model=BrandSpecOut, status_code=status.HTTP_201_CREATED)
async def create_spec(
    payload: BrandSpecCreate,
    principal: Principal = Depends(_WRITE_ROLES),
    session: AsyncSession = Depends(get_db),
) -> BrandSpecOut:
    spec = await service.create_brand_spec(session, principal.company_id, payload)
    rules = await service.get_rules(session, principal.company_id, spec.id)
    await record_audit(
        session,
        action="brand_spec.create",
        entity_type="brand_specification",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=spec.id,
        payload={"brand_name": spec.brand_name, "rules": len(rules)},
    )
    return _to_out(spec, rules)


@router.get("/{spec_id}", response_model=BrandSpecOut)
async def get_spec(
    spec_id: uuid.UUID,
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> BrandSpecOut:
    spec = await service.get_brand_spec(session, principal.company_id, spec_id)
    rules = await service.get_rules(session, principal.company_id, spec_id)
    return _to_out(spec, rules)


@router.post(
    "/{spec_id}/rules", response_model=AcceptanceRuleOut, status_code=status.HTTP_201_CREATED
)
async def add_rule(
    spec_id: uuid.UUID,
    payload: AcceptanceRuleIn,
    principal: Principal = Depends(_WRITE_ROLES),
    session: AsyncSession = Depends(get_db),
) -> AcceptanceRuleOut:
    rule = await service.add_rule(session, principal.company_id, spec_id, payload)
    await record_audit(
        session,
        action="brand_spec.add_rule",
        entity_type="brand_acceptance_rule",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=rule.id,
        payload={"test_method_code": rule.test_method_code, "fiber_code": rule.fiber_code},
    )
    return AcceptanceRuleOut.model_validate(rule)


@router.post("/{spec_id}/document", response_model=BrandSpecOut)
async def upload_capitolato(
    spec_id: uuid.UUID,
    file: UploadFile = File(...),
    principal: Principal = Depends(_WRITE_ROLES),
    session: AsyncSession = Depends(get_db),
) -> BrandSpecOut:
    """Attach the brand's capitolato document (PDF) to the spec."""
    spec = await service.get_brand_spec(session, principal.company_id, spec_id)
    data = await file.read()
    if not data:
        raise AppError("File vuoto.", code="empty_file")
    if len(data) > _MAX_DOC_BYTES:
        raise AppError("Documento troppo grande (max 10MB).", code="too_large")
    sha = hashlib.sha256(data).hexdigest()
    key = f"capitolati/{principal.company_id}/{spec_id}/{file.filename}"
    get_storage().put(key, data, file.content_type or "application/octet-stream")
    spec.meta = {
        **(spec.meta or {}),
        "capitolato_document": {
            "storage_key": key,
            "filename": file.filename,
            "sha256": sha,
            "size": len(data),
        },
    }
    await session.flush()
    rules = await service.get_rules(session, principal.company_id, spec_id)
    await record_audit(
        session,
        action="brand_spec.document_upload",
        entity_type="brand_specification",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=spec_id,
        payload={"filename": file.filename, "sha256": sha},
    )
    return _to_out(spec, rules)


@router.get("/{spec_id}/document")
async def download_capitolato(
    spec_id: uuid.UUID,
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    spec = await service.get_brand_spec(session, principal.company_id, spec_id)
    doc = (spec.meta or {}).get("capitolato_document")
    if not doc:
        raise NotFoundError("Nessun capitolato allegato a questa brand spec")
    data = get_storage().get(doc["storage_key"])
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{doc.get("filename", "capitolato")}"'
        },
    )
