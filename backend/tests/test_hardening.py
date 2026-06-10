from __future__ import annotations

import uuid


async def _register(client, email: str, company: str) -> dict:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert r.status_code == 201, r.text
    return r.json()


# ── No-DB ───────────────────────────────────────────────────────────────────
async def test_security_headers_present(client):
    r = await client.get("/healthz")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers.get("x-request-id")


async def test_login_rate_limited(client, require_db):
    # 10/min on login; the 11th attempt from the same client must be 429
    # (login hits the DB for the user lookup, so require_db refreshes the pool)
    codes = []
    for _ in range(12):
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "x"},
        )
        codes.append(r.status_code)
    assert 429 in codes


# ── DB ────────────────────────────────────────────────────────────────────────
async def test_refresh_rotation_and_reuse_detection(client, require_db):
    reg = await _register(client, f"rot-{uuid.uuid4().hex[:8]}@example.com", "Rot Co")
    r0 = reg["refresh_token"]

    # rotate: R0 -> R1
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": r0})
    assert resp.status_code == 200, resp.text
    r1 = resp.json()["refresh_token"]
    assert r1 != r0

    # replay R0 -> reuse detected -> 401 and whole family revoked
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": r0})
    assert resp.status_code == 401

    # R1 is now revoked too (family killed on reuse)
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": r1})
    assert resp.status_code == 401


async def test_logout_revokes_family(client, require_db):
    reg = await _register(client, f"out-{uuid.uuid4().hex[:8]}@example.com", "Out Co")
    r0 = reg["refresh_token"]

    resp = await client.post("/api/v1/auth/logout", json={"refresh_token": r0})
    assert resp.status_code == 200

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": r0})
    assert resp.status_code == 401


async def test_gdpr_export(client, require_db):
    email = f"gdpr-{uuid.uuid4().hex[:8]}@example.com"
    reg = await _register(client, email, "GDPR Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    r = await client.get("/api/v1/account/export", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == email
    assert any(m["company"] == "GDPR Co" for m in body["memberships"])


async def test_account_deletion_blocks_future_login(client, require_db):
    email = f"del-{uuid.uuid4().hex[:8]}@example.com"
    reg = await _register(client, email, "Del Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    r = await client.post("/api/v1/account/delete", headers=h)
    assert r.status_code == 200, r.text

    # deactivated user can no longer obtain new tokens
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    assert r.status_code == 401
