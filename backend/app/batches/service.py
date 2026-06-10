from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.batches.schemas import BatchCreate
from app.common.errors import ConflictError, NotFoundError
from app.db.models import MultifiberBatch, MultifiberStripProfile


async def create_batch(
    session: AsyncSession,
    company_id: uuid.UUID,
    created_by: uuid.UUID,
    data: BatchCreate,
) -> MultifiberBatch:
    batch = MultifiberBatch(
        company_id=company_id,
        batch_code=data.batch_code,
        supplier=data.supplier,
        strip_profile_code=data.strip_profile_code,
        opened_at=data.opened_at,
        expires_at=data.expires_at,
        reference_lab_values={k: v.model_dump() for k, v in data.reference_lab_values.items()},
        created_by=created_by,
    )
    session.add(batch)
    try:
        async with session.begin_nested():
            await session.flush()
    except IntegrityError as exc:
        raise ConflictError("A batch with this code already exists") from exc
    return batch


async def list_strip_profiles(session: AsyncSession) -> list[MultifiberStripProfile]:
    stmt = select(MultifiberStripProfile).order_by(MultifiberStripProfile.code)
    return list((await session.execute(stmt)).scalars().all())


async def list_batches(session: AsyncSession, company_id: uuid.UUID) -> list[MultifiberBatch]:
    stmt = (
        select(MultifiberBatch)
        .where(MultifiberBatch.company_id == company_id)
        .order_by(MultifiberBatch.created_at.desc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_batch(
    session: AsyncSession, company_id: uuid.UUID, batch_id: uuid.UUID
) -> MultifiberBatch:
    stmt = select(MultifiberBatch).where(
        MultifiberBatch.id == batch_id, MultifiberBatch.company_id == company_id
    )
    batch = (await session.execute(stmt)).scalar_one_or_none()
    if batch is None:
        raise NotFoundError("Batch not found")
    return batch


async def update_status(
    session: AsyncSession, company_id: uuid.UUID, batch_id: uuid.UUID, status: str
) -> MultifiberBatch:
    batch = await get_batch(session, company_id, batch_id)
    batch.status = status
    await session.flush()
    return batch
