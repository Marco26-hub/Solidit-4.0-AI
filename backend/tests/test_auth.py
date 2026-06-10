from __future__ import annotations

import uuid

import jwt
import pytest

from app.common.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    needs_rehash,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-password")
    assert hashed != "s3cret-password"
    assert verify_password("s3cret-password", hashed)
    assert not verify_password("wrong", hashed)
    assert not needs_rehash(hashed)


def test_access_token_roundtrip():
    uid, cid = uuid.uuid4(), uuid.uuid4()
    token = create_access_token(user_id=uid, company_id=cid, role="company_admin")
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == str(uid)
    assert payload["company_id"] == str(cid)
    assert payload["role"] == "company_admin"
    assert payload["type"] == "access"


def test_refresh_token_type_is_enforced():
    token = create_refresh_token(user_id=uuid.uuid4(), jti=uuid.uuid4(), family_id=uuid.uuid4())
    decode_token(token, expected_type="refresh")  # ok
    with pytest.raises(jwt.PyJWTError):
        decode_token(token, expected_type="access")


def test_tampered_token_rejected():
    token = create_access_token(user_id=uuid.uuid4())
    with pytest.raises(jwt.PyJWTError):
        decode_token(token + "x", expected_type="access")


async def test_protected_route_requires_auth(client):
    resp = await client.get("/api/v1/companies/me")
    assert resp.status_code == 401


async def test_protected_route_rejects_garbage_token(client):
    resp = await client.get("/api/v1/companies/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401
