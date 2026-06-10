"""Auth service: registration (tenant bootstrap), login, refresh, company
selection. These flows manage their own session/transaction because they need
to read the global ``users`` table and then set tenant RLS context manually."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import tokens
from app.auth.schemas import CompanyBrief, TokenResponse
from app.common.audit import record_audit
from app.common.errors import AuthError, ConflictError, ForbiddenError
from app.common.rls import apply_rls
from app.common.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import settings
from app.db.models import Company, CompanyMembership, User
from app.db.session import SessionLocal

DEFAULT_OWNER_ROLE = "company_admin"

# Fixed dummy hash so login does equal work whether or not the user exists
# (prevents timing-based account enumeration).
_DUMMY_PASSWORD_HASH = hash_password("constant-time-dummy-password")


@dataclass(frozen=True)
class _Membership:
    id: uuid.UUID
    name: str
    role: str


async def _get_user_by_email(session: AsyncSession, email: str) -> User | None:
    return (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()


async def _get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await session.get(User, user_id)


async def _load_memberships(session: AsyncSession, user_id: uuid.UUID) -> list[_Membership]:
    stmt = (
        select(Company.id, Company.name, CompanyMembership.role)
        .join(CompanyMembership, CompanyMembership.company_id == Company.id)
        .where(CompanyMembership.user_id == user_id)
        .order_by(Company.name)
    )
    rows = (await session.execute(stmt)).all()
    return [_Membership(id=r[0], name=r[1], role=r[2]) for r in rows]


def _select_company(
    memberships: list[_Membership], requested: uuid.UUID | None
) -> _Membership | None:
    if requested is not None:
        for m in memberships:
            if m.id == requested:
                return m
        raise ForbiddenError("User is not a member of the requested company")
    if len(memberships) == 1:
        return memberships[0]
    return None


async def _issue_tokens(
    session: AsyncSession,
    user_id: uuid.UUID,
    memberships: list[_Membership],
    selected: _Membership | None,
    *,
    family_id: uuid.UUID | None = None,
) -> TokenResponse:
    """Mint an access token + a rotated refresh token, persisting the refresh
    jti/family for reuse detection. Pass family_id to continue an existing
    rotation chain (refresh); omit it to start a new family (login/register)."""
    access = create_access_token(
        user_id=user_id,
        company_id=selected.id if selected else None,
        role=selected.role if selected else None,
    )
    family_id = family_id or uuid.uuid4()
    jti = uuid.uuid4()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    refresh = create_refresh_token(user_id=user_id, jti=jti, family_id=family_id)
    await tokens.issue(
        session, user_id=user_id, jti=jti, family_id=family_id, expires_at=expires_at
    )
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        company_id=selected.id if selected else None,
        role=selected.role if selected else None,
        companies=[CompanyBrief(id=m.id, name=m.name, role=m.role) for m in memberships],
    )


async def register(
    *, email: str, password: str, full_name: str | None, company_name: str, vat_number: str | None
) -> TokenResponse:
    async with SessionLocal() as session:
        async with session.begin():
            if await _get_user_by_email(session, email) is not None:
                raise ConflictError("Email already registered")

            user = User(email=email, password_hash=hash_password(password), full_name=full_name)
            session.add(user)
            await session.flush()  # users has no RLS; obtain user.id

            # Pre-generate the company id so we can set the tenant GUC BEFORE the
            # INSERT — then companies WITH CHECK (id = app_current_company_id())
            # is satisfied for the bootstrap create (no permissive WITH CHECK).
            company = Company(
                id=uuid.uuid4(),
                name=company_name,
                vat_number=vat_number,
                account_tier="trace",
            )
            await apply_rls(session, user_id=user.id, company_id=company.id)
            session.add(company)
            await session.flush()

            session.add(
                CompanyMembership(company_id=company.id, user_id=user.id, role=DEFAULT_OWNER_ROLE)
            )
            await session.flush()

            await record_audit(
                session,
                action="auth.register",
                entity_type="company",
                company_id=company.id,
                actor_user_id=user.id,
                entity_id=company.id,
            )
            membership = _Membership(id=company.id, name=company.name, role=DEFAULT_OWNER_ROLE)
            return await _issue_tokens(session, user.id, [membership], membership)


async def login(*, email: str, password: str, company_id: uuid.UUID | None) -> TokenResponse:
    async with SessionLocal() as session:
        async with session.begin():
            user = await _get_user_by_email(session, email)
            if user is None or not user.is_active:
                # constant-time: do the same hashing work even when the user is absent
                verify_password(password, _DUMMY_PASSWORD_HASH)
                raise AuthError("Invalid email or password")
            if not verify_password(password, user.password_hash):
                raise AuthError("Invalid email or password")

            await apply_rls(session, user_id=user.id)  # company unset → see all own memberships
            memberships = await _load_memberships(session, user.id)
            selected = _select_company(memberships, company_id)

            user.last_login_at = datetime.now(UTC)
            # Only write an audit row when a tenant is in context (audit_log is
            # strictly tenant-scoped). Multi-company users are audited at
            # /auth/select-company instead.
            if selected is not None:
                await apply_rls(session, user_id=user.id, company_id=selected.id)
                await record_audit(
                    session,
                    action="auth.login",
                    entity_type="user",
                    company_id=selected.id,
                    actor_user_id=user.id,
                    entity_id=user.id,
                )
            return await _issue_tokens(session, user.id, memberships, selected)


async def select_company(*, user_id: uuid.UUID, company_id: uuid.UUID) -> TokenResponse:
    async with SessionLocal() as session:
        async with session.begin():
            await apply_rls(session, user_id=user_id)
            memberships = await _load_memberships(session, user_id)
            selected = _select_company(memberships, company_id)
            await apply_rls(session, user_id=user_id, company_id=selected.id)
            await record_audit(
                session,
                action="auth.select_company",
                entity_type="company",
                company_id=selected.id,
                actor_user_id=user_id,
                entity_id=selected.id,
            )
            return await _issue_tokens(session, user_id, memberships, selected)


async def refresh(*, refresh_token: str, company_id: uuid.UUID | None) -> TokenResponse:
    """Rotate: consume the presented refresh token and issue a fresh pair in the
    same family. Replay of a consumed/revoked token revokes the whole family."""
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = uuid.UUID(payload["sub"])
        jti = uuid.UUID(payload["jti"])
        family_id = uuid.UUID(payload["family_id"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise AuthError("Invalid or expired refresh token") from exc

    async with SessionLocal() as session:
        async with session.begin():
            user = await _get_user_by_id(session, user_id)
            if user is None or not user.is_active:
                raise AuthError("User no longer active")
            await tokens.rotate(session, user_id=user_id, jti=jti, family_id=family_id)
            await apply_rls(session, user_id=user_id)
            memberships = await _load_memberships(session, user_id)
            selected = _select_company(memberships, company_id)
            if selected is not None:
                await apply_rls(session, user_id=user_id, company_id=selected.id)
            return await _issue_tokens(session, user_id, memberships, selected, family_id=family_id)


async def logout(*, refresh_token: str) -> None:
    """Revoke the presented token's whole family. Idempotent / never errors."""
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        family_id = uuid.UUID(payload["family_id"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return
    async with SessionLocal() as session:
        async with session.begin():
            await tokens.revoke_family(session, family_id)
