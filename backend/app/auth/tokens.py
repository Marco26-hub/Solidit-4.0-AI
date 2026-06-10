"""Refresh-token server-side store: issue, rotate (with reuse detection),
revoke. Backs token rotation/revocation so a leaked refresh token can be
contained (see SECURITY hardening)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AuthError
from app.db.models import RefreshToken


async def issue(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    jti: uuid.UUID,
    family_id: uuid.UUID,
    expires_at: datetime,
) -> None:
    session.add(RefreshToken(user_id=user_id, jti=jti, family_id=family_id, expires_at=expires_at))
    await session.flush()


async def revoke_family(session: AsyncSession, family_id: uuid.UUID) -> None:
    await session.execute(
        update(RefreshToken).where(RefreshToken.family_id == family_id).values(revoked=True)
    )


async def _revoke_family_committed(family_id: uuid.UUID) -> None:
    """Revoke a family in its own committed transaction. Used on reuse detection,
    where the caller's transaction is about to roll back (we raise), so the
    revocation must persist independently."""
    from app.db.session import SessionLocal

    async with SessionLocal() as session:
        async with session.begin():
            await revoke_family(session, family_id)


async def revoke_user(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Revoke all of a user's refresh tokens (e.g. on password change/logout-all)."""
    await session.execute(
        update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True)
    )


async def rotate(
    session: AsyncSession, *, user_id: uuid.UUID, jti: uuid.UUID, family_id: uuid.UUID
) -> None:
    """Consume the presented refresh jti. Raises AuthError if it's unknown,
    already used, revoked or expired — and on reuse revokes the whole family."""
    row = (
        await session.execute(select(RefreshToken).where(RefreshToken.jti == jti))
    ).scalar_one_or_none()

    if row is None or row.user_id != user_id or row.family_id != family_id:
        await _revoke_family_committed(family_id)  # committed: caller will roll back
        raise AuthError("Invalid refresh token")

    now = datetime.now(UTC)
    if row.revoked or row.used_at is not None or row.expires_at <= now:
        # replay of a consumed/revoked token => treat as theft, revoke the family
        await _revoke_family_committed(family_id)
        raise AuthError("Refresh token reuse detected; session revoked")

    row.used_at = now


async def mark_replaced(session: AsyncSession, *, old_jti: uuid.UUID, new_jti: uuid.UUID) -> None:
    await session.execute(
        update(RefreshToken).where(RefreshToken.jti == old_jti).values(replaced_by_jti=new_jti)
    )
