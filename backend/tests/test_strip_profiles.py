from __future__ import annotations

import uuid


async def _register(client, email, company):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_strip_profiles_seeded_and_differ(client, require_db):
    reg = await _register(client, f"strip-{uuid.uuid4().hex[:8]}@example.com", "Strip Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    r = await client.get("/api/v1/multifiber-batches/strip-profiles", headers=h)
    assert r.status_code == 200, r.text
    by_code = {p["code"]: p for p in r.json()}
    assert {"AATCC_MULTIFIBER_10", "ISO_105_F10_DW", "ISO_105_F10_TV"} <= set(by_code)

    # the standards genuinely differ (this is the whole point)
    assert by_code["AATCC_MULTIFIBER_10"]["fibers"][0] == "acetate"
    assert by_code["ISO_105_F10_DW"]["fibers"][0] == "diacetate"
    assert by_code["ISO_105_F10_TV"]["fibers"][0] == "triacetate"
    assert "viscose" in by_code["ISO_105_F10_TV"]["fibers"]
    assert "wool" in by_code["ISO_105_F10_DW"]["fibers"]


async def test_batch_zero_records_strip_profile(client, require_db):
    reg = await _register(client, f"strip2-{uuid.uuid4().hex[:8]}@example.com", "Strip2 Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    r = await client.post(
        "/api/v1/multifiber-batches",
        json={
            "batch_code": "B-DW-1",
            "strip_profile_code": "ISO_105_F10_DW",
            "reference_lab_values": {
                "diacetate": {"L": 95.1, "a": 0.2, "b": 1.1},
                "cotton": {"L": 96.0, "a": 0.1, "b": 0.9},
                "polyamide": {"L": 94.5, "a": 0.3, "b": 1.3},
            },
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    assert r.json()["strip_profile_code"] == "ISO_105_F10_DW"
