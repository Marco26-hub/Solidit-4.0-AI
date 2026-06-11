from __future__ import annotations

import uuid

from app.db.models import ValidationSample
from app.validation.service import compute_metrics


# ── pure stats (no DB) ────────────────────────────────────────────────────────
def _s(sw, ref):
    return ValidationSample(sample_code="x", software_grade=sw, reference_grade=ref)


def test_compute_metrics_basic():
    samples = [_s(4.5, 4.5), _s(4.0, 4.5), _s(3.0, 3.5), _s(5.0, 5.0)]
    m = compute_metrics(samples)
    assert m["scored"] == 4
    # |dev|: 0, 0.5, 0.5, 0 -> all within ±0.5 -> 100%
    assert m["pct_within_half_grade"] == 100.0
    assert m["mean_abs_grade_dev"] == 0.25
    assert m["indicative_pass"] is True


def test_compute_metrics_flags_below_threshold():
    samples = [_s(5.0, 3.0), _s(4.0, 2.0), _s(5.0, 5.0)]  # 2 large deviations
    m = compute_metrics(samples)
    assert m["pct_within_half_grade"] < 90.0
    assert m["indicative_pass"] is False
    assert m["max_abs_grade_dev"] == 2.0


def test_compute_metrics_empty():
    assert compute_metrics([])["scored"] == 0


# ── full campaign flow (DB) ───────────────────────────────────────────────────
async def _register(client, email, company):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_validation_campaign_flow(client, require_db):
    reg = await _register(client, f"vrun-{uuid.uuid4().hex[:8]}@example.com", "Valid Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    run = (
        await client.post(
            "/api/v1/validation-runs", json={"name": "Pilota 30 campioni"}, headers=h
        )
    ).json()
    assert run["status"] == "pending"

    for i, (sw, ref) in enumerate([(4.5, 4.5), (4.0, 4.5), (3.5, 3.5), (2.0, 2.5)]):
        r = await client.post(
            f"/api/v1/validation-runs/{run['id']}/samples",
            json={
                "sample_code": f"S{i}",
                "reference_method": "spectrophotometer",
                "software_grade": sw,
                "reference_grade": ref,
            },
            headers=h,
        )
        assert r.status_code == 201, r.text

    r = await client.post(f"/api/v1/validation-runs/{run['id']}/compute", headers=h)
    assert r.status_code == 200, r.text
    m = r.json()["metrics"]
    assert m["scored"] == 4
    assert m["pct_within_half_grade"] == 100.0
    assert "rmse" in m and "bias" in m

    detail = (await client.get(f"/api/v1/validation-runs/{run['id']}", headers=h)).json()
    assert detail["status"] == "computed"
    assert len(detail["samples"]) == 4
