from __future__ import annotations

import uuid

from app.reports.pdf import build_report_pdf
from app.reports.service import canonical_hash

_SAMPLE = {
    "report_number": "RPT-2026-DEADBEEF",
    "company": {"id": "c1", "name": "Tintoria Demo"},
    "test_job": {
        "id": "j1",
        "article_code": "ART1",
        "lot_code": "LOT1",
        "barcode": None,
        "status": "failed",
    },
    "test_method_code": "ISO_105_X12",
    "brand": {"id": "b1", "name": "Brand X"},
    "measurement": {
        "algorithm_version": "manual-entry-0.1.0",
        "results": {"test_method_code": "ISO_105_X12", "fibers": {"cotton": {"delta_e": 2.5}}},
        "pass_fail": {
            "overall_pass": False,
            "evaluated": True,
            "per_fiber": {
                "cotton": {
                    "pass": False,
                    "checks": [{"metric": "delta_e", "value": 2.5, "limit": 1.0, "ok": False}],
                }
            },
            "violations": [
                {
                    "fiber": "cotton",
                    "metric": "delta_e",
                    "value": 2.5,
                    "limit": 1.0,
                    "severity": "blocking",
                }
            ],
        },
    },
    "generated_at": "2026-06-09T00:00:00+00:00",
    "generated_by": "u1",
}


# ── No-DB unit tests (exercise ReportLab + hashing) ─────────────────────────────
def test_canonical_hash_is_key_order_independent():
    a = {"x": 1, "y": {"b": 2, "a": 3}}
    b = {"y": {"a": 3, "b": 2}, "x": 1}
    assert canonical_hash(a) == canonical_hash(b)


def test_canonical_hash_changes_on_tamper():
    h1 = canonical_hash(_SAMPLE)
    tampered = {**_SAMPLE, "report_number": "RPT-2026-FORGED"}
    assert h1 != canonical_hash(tampered)


def test_build_pdf_smoke():
    sha = canonical_hash(_SAMPLE)
    pdf = build_report_pdf(_SAMPLE, sha, "http://localhost:8000/api/v1/reports/x/verify")
    assert isinstance(pdf, bytes)
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 1000


# ── Full report flow (requires Postgres) ────────────────────────────────────────
async def _register(client, email, company):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_report_generate_verify_download(client, require_db):
    reg = await _register(client, f"rep-{uuid.uuid4().hex[:8]}@example.com", "Report Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    spec = (
        await client.post(
            "/api/v1/brand-specifications",
            json={
                "brand_name": "Brand R",
                "rules": [
                    {
                        "test_method_code": "ISO_105_X12",
                        "fiber_code": "cotton",
                        "max_delta_e": 1.0,
                        "severity": "blocking",
                    }
                ],
            },
            headers=h,
        )
    ).json()

    job = (
        await client.post(
            "/api/v1/test-jobs",
            json={
                "brand_specification_id": spec["id"],
                "test_method_code": "ISO_105_X12",
                "article_code": "A",
                "lot_code": "L",
            },
            headers=h,
        )
    ).json()

    await client.post(
        f"/api/v1/test-jobs/{job['id']}/manual-result",
        json={"test_method_code": "ISO_105_X12", "fibers": {"cotton": {"delta_e": 2.5}}},
        headers=h,
    )

    # generate report
    r = await client.post(f"/api/v1/test-jobs/{job['id']}/reports", headers=h)
    assert r.status_code == 201, r.text
    report = r.json()
    assert report["report_number"].startswith("RPT-")
    assert len(report["sha256_hash"]) == 64

    # verify -> integrity seal holds
    r = await client.get(f"/api/v1/reports/{report['id']}/verify", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["recomputed_hash"] == report["sha256_hash"]

    # ledger lists it
    r = await client.get("/api/v1/reports", headers=h)
    assert any(x["id"] == report["id"] for x in r.json())

    # download is a real PDF
    r = await client.get(f"/api/v1/reports/{report['id']}/download", headers=h)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:5] == b"%PDF-"

    # finalize (lock) the report -> official immutable emission
    r = await client.post(f"/api/v1/reports/{report['id']}/finalize", headers=h)
    assert r.status_code == 200, r.text
    locked = r.json()
    assert locked["status"] == "locked"
    assert locked["locked_at"] is not None

    # a locked report blocks emitting another one over the same job
    r = await client.post(f"/api/v1/test-jobs/{job['id']}/reports", headers=h)
    assert r.status_code == 409, r.text
    assert "locked" in r.text.lower() or "bloccato" in r.text.lower()
