from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_tenant_principal, require_role
from app.departments import service
from app.departments.schemas import DepartmentCreate, DepartmentOut, DepartmentUpdate

router = APIRouter(prefix="/api/v1/departments", tags=["departments"])

_WRITE_ROLES = require_role("company_admin", "lab_manager")


@router.get("", response_model=list[DepartmentOut])
async def list_departments(
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[DepartmentOut]:
    rows = await service.list_departments(session, principal.company_id)
    return [DepartmentOut.model_validate(d) for d in rows]


@router.post("", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
async def create_department(
    payload: DepartmentCreate,
    principal: Principal = Depends(_WRITE_ROLES),
    session: AsyncSession = Depends(get_db),
) -> DepartmentOut:
    dept = await service.create_department(session, principal.company_id, payload)
    await record_audit(
        session,
        action="department.create",
        entity_type="department",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=dept.id,
        payload={"code": dept.code, "name": dept.name},
    )
    return DepartmentOut.model_validate(dept)


@router.patch("/{department_id}", response_model=DepartmentOut)
async def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    principal: Principal = Depends(_WRITE_ROLES),
    session: AsyncSession = Depends(get_db),
) -> DepartmentOut:
    dept = await service.update_department(session, principal.company_id, department_id, payload)
    await record_audit(
        session,
        action="department.update",
        entity_type="department",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=department_id,
        payload=payload.model_dump(exclude_none=True),
    )
    return DepartmentOut.model_validate(dept)
