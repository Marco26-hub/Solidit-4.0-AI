from __future__ import annotations

import uuid


async def _register(client, email, company):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_iso_methods_seeded(client, require_db):
    reg = await _register(client, f"m-{uuid.uuid4().hex[:8]}@example.com", "Methods Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    codes = {m["code"] for m in (await client.get("/api/v1/test-methods", headers=h)).json()}
    # perspiration (37°C), sea water, chlorinated water — colour-change/multifibre family
    for c in ("ISO_105_E02", "ISO_105_E03", "ISO_105_E04", "ISO_105_E01"):
        assert c in codes, c


async def test_method_reference_document_upload_download(client, require_db):
    reg = await _register(client, f"md-{uuid.uuid4().hex[:8]}@example.com", "Norm Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    # no document yet -> 404
    r = await client.get("/api/v1/test-methods/ISO_105_E04/document", headers=h)
    assert r.status_code == 404, r.text

    pdf = b"%PDF-1.4\n% fake licensed norm copy\n"
    r = await client.post(
        "/api/v1/test-methods/ISO_105_E04/document",
        files={"file": ("ISO105-E04.pdf", pdf, "application/pdf")},
        headers=h,
    )
    assert r.status_code == 201, r.text
    assert r.json()["test_method_code"] == "ISO_105_E04"

    # listed
    docs = (await client.get("/api/v1/test-methods/documents", headers=h)).json()
    assert any(d["test_method_code"] == "ISO_105_E04" for d in docs)

    # download returns the bytes
    r = await client.get("/api/v1/test-methods/ISO_105_E04/document", headers=h)
    assert r.status_code == 200, r.text
    assert r.content == pdf

    # unknown method code -> 404 on upload
    r = await client.post(
        "/api/v1/test-methods/NOPE_999/document",
        files={"file": ("x.pdf", pdf, "application/pdf")},
        headers=h,
    )
    assert r.status_code == 404, r.text
