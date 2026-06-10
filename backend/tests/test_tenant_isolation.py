"""The most important test: PostgreSQL RLS isolates tenants. Requires a
migrated database (skipped automatically when Postgres is unavailable)."""

from __future__ import annotations

import uuid

from sqlalchemy import text


async def _register(client, email: str, company: str) -> dict:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _auth(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}


async def test_tenant_cannot_see_other_tenant_data(client, require_db):
    a = await _register(client, f"a-{uuid.uuid4().hex[:8]}@example.com", "Company A")
    b = await _register(client, f"b-{uuid.uuid4().hex[:8]}@example.com", "Company B")

    # Company A creates a department.
    resp = await client.post(
        "/api/v1/departments",
        json={"code": "TINT", "name": "Tintoria"},
        headers=_auth(a),
    )
    assert resp.status_code == 201, resp.text

    # A sees its own department.
    resp = await client.get("/api/v1/departments", headers=_auth(a))
    assert resp.status_code == 200
    assert any(d["code"] == "TINT" for d in resp.json())

    # B must NOT see A's department.
    resp = await client.get("/api/v1/departments", headers=_auth(b))
    assert resp.status_code == 200
    assert all(d["code"] != "TINT" for d in resp.json())

    # /companies/me returns each caller's own company only.
    me_a = (await client.get("/api/v1/companies/me", headers=_auth(a))).json()
    me_b = (await client.get("/api/v1/companies/me", headers=_auth(b))).json()
    assert me_a["name"] == "Company A"
    assert me_b["name"] == "Company B"


async def test_rls_fails_closed_without_tenant_context(require_db):
    """With NO tenant GUC set, the app role sees zero companies (fail closed).
    This only holds because the app connects as a NON-superuser role."""
    from app.db.session import SessionLocal

    async with SessionLocal() as session:
        async with session.begin():
            visible = (await session.execute(text("SELECT count(*) FROM companies"))).scalar()
    assert visible == 0


async def test_cross_company_membership_forbidden(client, require_db):
    a = await _register(client, f"a-{uuid.uuid4().hex[:8]}@example.com", "Company A")
    b = await _register(client, f"b-{uuid.uuid4().hex[:8]}@example.com", "Company B")

    # A's user id from its token; try to select B's company with A's bearer token.
    import jwt as _jwt

    from app.config import settings

    b_company_id = b["company_id"]
    resp = await client.post(
        "/api/v1/auth/select-company",
        json={"company_id": b_company_id},
        headers=_auth(a),
    )
    assert resp.status_code == 403, resp.text

    # sanity: token decodes and belongs to A (not B)
    payload = _jwt.decode(
        a["access_token"], settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    assert payload["company_id"] == a["company_id"]


async def test_rls_rejects_forged_foreign_membership(client, require_db):
    """The critical RLS guard: inside tenant A's context, the app role must NOT be
    able to INSERT a company_memberships row pointing at tenant B (self-enrollment /
    cross-tenant takeover). WITH CHECK (company_id = app_current_company_id())."""
    import jwt as _jwt
    from sqlalchemy.exc import DBAPIError

    from app.common.rls import apply_rls
    from app.config import settings
    from app.db.session import SessionLocal

    a = await _register(client, f"a-{uuid.uuid4().hex[:8]}@example.com", "Company A")
    b = await _register(client, f"b-{uuid.uuid4().hex[:8]}@example.com", "Company B")
    a_user = _jwt.decode(
        a["access_token"], settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )["sub"]
    a_company = a["company_id"]
    b_company = b["company_id"]

    raised = False
    async with SessionLocal() as session:
        try:
            async with session.begin():
                # tenant context = Company A
                await apply_rls(
                    session,
                    user_id=uuid.UUID(a_user),
                    company_id=uuid.UUID(a_company),
                )
                # attempt to enroll A's user into Company B as admin -> must be blocked
                await session.execute(
                    text(
                        "INSERT INTO company_memberships (company_id, user_id, role) "
                        "VALUES (:c, :u, 'company_admin')"
                    ),
                    {"c": b_company, "u": a_user},
                )
        except DBAPIError:
            raised = True
    assert raised, "RLS WITH CHECK must reject a membership row for a foreign tenant"
