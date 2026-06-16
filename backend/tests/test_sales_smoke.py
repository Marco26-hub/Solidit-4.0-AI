from __future__ import annotations

import uuid


async def _register(client, email: str, company: str) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_sales_smoke_report_public_verify_and_billing_fallback(client, require_db):
    health = await client.get("/healthz")
    assert health.status_code == 200
    assert health.headers["x-content-type-options"] == "nosniff"
    assert health.headers["x-frame-options"] == "DENY"

    registration = await _register(
        client,
        f"sales-{uuid.uuid4().hex[:8]}@example.com",
        "Sales Demo Co",
    )
    headers = {"Authorization": f"Bearer {registration['access_token']}"}

    spec_response = await client.post(
        "/api/v1/brand-specifications",
        json={
            "brand_name": "Brand Demo",
            "rules": [
                {
                    "test_method_code": "ISO_105_X12",
                    "fiber_code": "cotton",
                    "max_delta_e": 1.0,
                    "severity": "blocking",
                }
            ],
        },
        headers=headers,
    )
    assert spec_response.status_code == 201, spec_response.text
    spec = spec_response.json()

    job_response = await client.post(
        "/api/v1/test-jobs",
        json={
            "brand_specification_id": spec["id"],
            "test_method_code": "ISO_105_X12",
            "article_code": "DEMO-ART",
            "lot_code": "DEMO-LOT",
        },
        headers=headers,
    )
    assert job_response.status_code == 201, job_response.text
    job = job_response.json()

    result_response = await client.post(
        f"/api/v1/test-jobs/{job['id']}/manual-result",
        json={"test_method_code": "ISO_105_X12", "fibers": {"cotton": {"delta_e": 0.7}}},
        headers=headers,
    )
    assert result_response.status_code == 201, result_response.text

    report_response = await client.post(f"/api/v1/test-jobs/{job['id']}/reports", headers=headers)
    assert report_response.status_code == 201, report_response.text
    report = report_response.json()
    assert report["report_number"].startswith("RPT-")
    assert len(report["sha256_hash"]) == 64

    finalize_response = await client.post(
        f"/api/v1/reports/{report['id']}/finalize",
        headers=headers,
    )
    assert finalize_response.status_code == 200, finalize_response.text
    assert finalize_response.json()["status"] == "locked"

    public_response = await client.get(
        f"/api/v1/public/reports/{report['id']}/verify?h={report['sha256_hash']}"
    )
    assert public_response.status_code == 200, public_response.text
    public_body = public_response.json()
    assert public_body["valid"] is True
    assert public_body["locked"] is True
    assert public_body["company_name"] == "Sales Demo Co"

    invalid_public_response = await client.get(
        f"/api/v1/public/reports/{report['id']}/verify?h=not-the-seal"
    )
    assert invalid_public_response.status_code == 200, invalid_public_response.text
    assert invalid_public_response.json() == {
        "valid": False,
        "report_number": None,
        "company_name": None,
        "issued_at": None,
        "locked": None,
        "sha256_hash": None,
    }

    checkout_response = await client.post(
        "/api/v1/billing/checkout",
        json={"plan": "trace"},
        headers=headers,
    )
    assert checkout_response.status_code == 400, checkout_response.text
    assert "stripe" in checkout_response.text.lower() or "no_price" in checkout_response.text
