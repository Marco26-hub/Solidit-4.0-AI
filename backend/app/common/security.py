"""Password hashing (Argon2) and JWT access/refresh tokens."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.config import settings

_hasher = PasswordHasher()

TokenType = Literal["access", "refresh"]


# ── Passwords ────────────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    try:
        return _hasher.check_needs_rehash(hashed)
    except InvalidHashError:
        return True


# ── JWT ──────────────────────────────────────────────────────────────────────
def _encode(
    *,
    subject: uuid.UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    extra: dict[str, Any] | None = None,
    jti: uuid.UUID | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(jti) if jti else str(uuid.uuid4()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(
    *, user_id: uuid.UUID, company_id: uuid.UUID | None = None, role: str | None = None
) -> str:
    extra: dict[str, Any] = {}
    if company_id is not None:
        extra["company_id"] = str(company_id)
    if role is not None:
        extra["role"] = role
    return _encode(
        subject=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra=extra,
    )


def create_refresh_token(*, user_id: uuid.UUID, jti: uuid.UUID, family_id: uuid.UUID) -> str:
    return _encode(
        subject=user_id,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        extra={"family_id": str(family_id)},
        jti=jti,
    )


def decode_token(token: str, *, expected_type: TokenType | None = None) -> dict[str, Any]:
    """Decode and validate a JWT. Raises ``jwt.PyJWTError`` on failure."""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if expected_type is not None and payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"expected {expected_type} token")
    return payload
