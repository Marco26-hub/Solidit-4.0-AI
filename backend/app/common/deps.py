"""FastAPI dependencies: auth principal + tenant-scoped DB session."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AuthError, ForbiddenError
from app.common.rls import apply_rls
from app.common.security import decode_token
from app.db.session import SessionLocal

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    user_id: uuid.UUID
    company_id: uuid.UUID | None = None
    role: str | None = None


async def get_principal(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Principal:
    if creds is None:
        raise AuthError("Missing bearer token")
    try:
        payload = decode_token(creds.credentials, expected_type="access")
        company_raw = payload.get("company_id")
        principal = Principal(
            user_id=uuid.UUID(payload["sub"]),
            company_id=uuid.UUID(company_raw) if company_raw else None,
            role=payload.get("role"),
        )
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        # malformed-but-signed claims must be 401, not a 500
        raise AuthError("Invalid or expired token") from exc
    return principal


async def get_db(principal: Principal = Depends(get_principal)) -> AsyncIterator[AsyncSession]:
    """Tenant-scoped session. Opens one transaction per request and sets the RLS
    GUCs on it; commits on success, rolls back on error."""
    async with SessionLocal() as session:
        async with session.begin():
            await apply_rls(session, user_id=principal.user_id, company_id=principal.company_id)
            # Re-validate membership on every tenant request: the access token's
            # company_id is only a hint. If the user was removed from the company,
            # their still-valid token must stop granting access immediately.
            if principal.company_id is not None:
                still_member = (
                    await session.execute(
                        text(
                            "SELECT 1 FROM company_memberships "
                            "WHERE user_id = app_current_user_id() "
                            "AND company_id = app_current_company_id()"
                        )
                    )
                ).first()
                if still_member is None:
                    raise ForbiddenError("Membership revoked or company not accessible")
            yield session


async def get_public_db() -> AsyncIterator[AsyncSession]:
    """Unauthenticated session — NO tenant context set. Only rows under an RLS
    policy that permits anonymous reads (e.g. report_verifications USING true) are
    visible; every tenant table returns nothing because app_current_company_id()
    is NULL. Used by public, non-sensitive endpoints."""
    async with SessionLocal() as session:
        async with session.begin():
            yield session


async def get_tenant_principal(principal: Principal = Depends(get_principal)) -> Principal:
    """Require that a tenant (company) is selected in the token."""
    if principal.company_id is None:
        raise ForbiddenError("No company selected. Re-authenticate selecting a company.")
    return principal


def require_role(*roles: str) -> Callable[[Principal], Principal]:
    async def _checker(principal: Principal = Depends(get_tenant_principal)) -> Principal:
        if principal.role not in roles:
            raise ForbiddenError(f"Requires one of roles: {', '.join(roles)}")
        return principal

    return _checker
