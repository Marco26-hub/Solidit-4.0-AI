from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ForbiddenError, NotFoundError
from app.companies.schemas import CompanyUpdate
from app.db.models import Company


async def get_company(session: AsyncSession, company_id: uuid.UUID) -> Company:
    company = (
        await session.execute(select(Company).where(Company.id == company_id))
    ).scalar_one_or_none()
    if company is None:
        # Either it doesn't exist or RLS hid it — same opaque error either way.
        raise NotFoundError("Company not found")
    return company


async def update_company(
    session: AsyncSession, company_id: uuid.UUID, data: CompanyUpdate
) -> Company:
    company = await get_company(session, company_id)
    if data.name is not None:
        company.name = data.name
    if data.vat_number is not None:
        company.vat_number = data.vat_number
    if data.settings is not None:
        company.settings = data.settings
    if data.active_departments is not None:
        company.active_departments = data.active_departments
    await session.flush()
    return company


def ensure_same_company(token_company_id: uuid.UUID, path_company_id: uuid.UUID) -> None:
    if token_company_id != path_company_id:
        raise ForbiddenError("Token is not scoped to this company")
