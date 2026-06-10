from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError, NotFoundError
from app.db.models import Department
from app.departments.schemas import DepartmentCreate, DepartmentUpdate


async def list_departments(session: AsyncSession, company_id: uuid.UUID) -> list[Department]:
    stmt = select(Department).where(Department.company_id == company_id).order_by(Department.code)
    return list((await session.execute(stmt)).scalars().all())


async def create_department(
    session: AsyncSession, company_id: uuid.UUID, data: DepartmentCreate
) -> Department:
    dept = Department(company_id=company_id, code=data.code, name=data.name, meta=data.metadata)
    session.add(dept)
    try:
        async with session.begin_nested():  # SAVEPOINT: keep the txn usable on conflict
            await session.flush()
    except IntegrityError as exc:
        raise ConflictError("A department with this code already exists") from exc
    return dept


async def get_department(
    session: AsyncSession, company_id: uuid.UUID, department_id: uuid.UUID
) -> Department:
    stmt = select(Department).where(
        Department.id == department_id, Department.company_id == company_id
    )
    dept = (await session.execute(stmt)).scalar_one_or_none()
    if dept is None:
        raise NotFoundError("Department not found")
    return dept


async def update_department(
    session: AsyncSession,
    company_id: uuid.UUID,
    department_id: uuid.UUID,
    data: DepartmentUpdate,
) -> Department:
    dept = await get_department(session, company_id, department_id)
    if data.name is not None:
        dept.name = data.name
    if data.metadata is not None:
        dept.meta = data.metadata
    if data.is_active is not None:
        dept.is_active = data.is_active
    await session.flush()
    return dept
