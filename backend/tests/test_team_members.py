from __future__ import annotations

import uuid


async def _register(client, email, company):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _login(client, email, password="password123"):
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


async def test_admin_adds_operator_and_roles_are_enforced(client, require_db):
    tag = uuid.uuid4().hex[:8]
    reg = await _register(client, f"boss-{tag}@example.com", "Team Co")
    admin = {"Authorization": f"Bearer {reg['access_token']}"}

    # admin creates an operator member
    r = await client.post(
        "/api/v1/companies/members",
        json={"email": f"op-{tag}@example.com", "password": "operatore1", "role": "operator"},
        headers=admin,
    )
    assert r.status_code == 201, r.text
    assert r.json()["role"] == "operator"

    # duplicate → 409
    r = await client.post(
        "/api/v1/companies/members",
        json={"email": f"op-{tag}@example.com", "password": "operatore1", "role": "operator"},
        headers=admin,
    )
    assert r.status_code == 409

    # members list shows both
    r = await client.get("/api/v1/companies/members", headers=admin)
    assert r.status_code == 200
    roles = {m["email"]: m["role"] for m in r.json()}
    assert roles[f"op-{tag}@example.com"] == "operator"
    assert roles[f"boss-{tag}@example.com"] == "company_admin"

    # operator logs in, lands in the same tenant with role=operator
    op_login = await _login(client, f"op-{tag}@example.com", "operatore1")
    assert op_login["role"] == "operator"
    op = {"Authorization": f"Bearer {op_login['access_token']}"}

    # operator CAN create a test job (the work)...
    r = await client.post(
        "/api/v1/test-jobs", json={"test_method_code": "ISO_105_E04"}, headers=op
    )
    assert r.status_code == 201, r.text

    # ...but CANNOT approve: report generation and member management are denied
    job_id = r.json()["id"]
    r = await client.post(f"/api/v1/test-jobs/{job_id}/reports", headers=op)
    assert r.status_code == 403
    r = await client.post(
        "/api/v1/companies/members",
        json={"email": f"x-{tag}@example.com", "password": "password123", "role": "operator"},
        headers=op,
    )
    assert r.status_code == 403


async def test_member_removal_guards(client, require_db):
    tag = uuid.uuid4().hex[:8]
    reg = await _register(client, f"solo-{tag}@example.com", "Solo Co")
    admin = {"Authorization": f"Bearer {reg['access_token']}"}

    # cannot remove yourself (and, being the last admin, the company stays safe)
    r = await client.get("/api/v1/companies/members", headers=admin)
    my_id = r.json()[0]["user_id"]
    r = await client.delete(f"/api/v1/companies/members/{my_id}", headers=admin)
    assert r.status_code == 400, r.text
    assert len((await client.get("/api/v1/companies/members", headers=admin)).json()) == 1

    # add + remove an operator; their tenant access dies immediately
    r = await client.post(
        "/api/v1/companies/members",
        json={"email": f"tmp-{tag}@example.com", "password": "password123", "role": "operator"},
        headers=admin,
    )
    uid = r.json()["user_id"]
    tmp_login = await _login(client, f"tmp-{tag}@example.com")
    tmp = {"Authorization": f"Bearer {tmp_login['access_token']}"}
    assert (await client.get("/api/v1/test-jobs", headers=tmp)).status_code == 200
    assert (
        await client.delete(f"/api/v1/companies/members/{uid}", headers=admin)
    ).status_code == 204
    # membership revoked → token no longer grants tenant access (get_db re-check)
    assert (await client.get("/api/v1/test-jobs", headers=tmp)).status_code == 403


async def test_operator_authorization_registry_and_flags(client, require_db):
    tag = uuid.uuid4().hex[:8]
    reg = await _register(client, f"resp-{tag}@example.com", "Auth Co")
    admin = {"Authorization": f"Bearer {reg['access_token']}"}

    # manual result WITHOUT any authorization → operator flagged as not authorized
    job = (
        await client.post(
            "/api/v1/test-jobs", json={"test_method_code": "ISO_105_E04"}, headers=admin
        )
    ).json()
    r = await client.post(
        f"/api/v1/test-jobs/{job['id']}/manual-result",
        json={
            "test_method_code": "ISO_105_E04",
            "fibers": {"cotton": {"delta_e": 1.2, "gray_scale_grade": 4.5}},
        },
        headers=admin,
    )
    assert r.status_code == 201, r.text
    op_info = r.json()["results"]["operator"]
    assert op_info["authorized"] is False
    assert "6.2" in op_info["detail"]

    # admin registers an authorization for themselves on the method
    me = (await client.get("/api/v1/companies/members", headers=admin)).json()[0]["user_id"]
    r = await client.post(
        "/api/v1/companies/authorizations",
        json={"user_id": me, "method_code": "ISO_105_E04", "training_notes": "corso interno"},
        headers=admin,
    )
    assert r.status_code == 201, r.text

    # a new result on the same method is now marked authorized
    r = await client.post(
        f"/api/v1/test-jobs/{job['id']}/manual-result",
        json={
            "test_method_code": "ISO_105_E04",
            "fibers": {"cotton": {"delta_e": 1.0, "gray_scale_grade": 4.5}},
        },
        headers=admin,
    )
    assert r.status_code == 201
    assert r.json()["results"]["operator"]["authorized"] is True

    # readiness now shows the operators item as done
    rd = (await client.get("/api/v1/accreditation/readiness", headers=admin)).json()
    ops = next(i for i in rd["items"] if i["key"] == "operators")
    assert ops["status"] == "done"

    # revoke → back to not authorized on the next result
    auths = (await client.get("/api/v1/companies/authorizations", headers=admin)).json()
    assert (
        await client.post(
            f"/api/v1/companies/authorizations/{auths[0]['id']}/revoke", headers=admin
        )
    ).status_code == 204
    r = await client.post(
        f"/api/v1/test-jobs/{job['id']}/manual-result",
        json={
            "test_method_code": "ISO_105_E04",
            "fibers": {"cotton": {"delta_e": 1.1, "gray_scale_grade": 4.5}},
        },
        headers=admin,
    )
    assert r.json()["results"]["operator"]["authorized"] is False
