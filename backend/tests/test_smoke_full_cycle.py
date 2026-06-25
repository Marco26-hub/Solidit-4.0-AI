"""End-to-end smoke test of the FULL quality-control workflow, from tenant
bootstrap to the final, sendable report.

Cycle exercised (the real operator journey):
  register tenant+admin
    -> brand specification + acceptance rule (pass/fail thresholds)
    -> article + production variant (reference Lab)
    -> multifibre batch zero (reference Lab per fibre)
    -> calibration references (grey scale + white tile + blue wool) with validity
    -> test job (linked to brand spec + method + article/variant)
    -> capture session + strip photo upload + Vision analysis (staining)
    -> manual graded result (human-in-the-loop verification) -> pass/fail
    -> generate report (number + SHA-256 seal)
    -> authenticated integrity verify (valid)
    -> finalize / lock
    -> re-emission blocked (409)
    -> public verification (QR hash) valid / invalid
    -> PDF download (the deliverable to send)

This is a single happy-path assertion chain: if it stays green, the whole
trace+vision+report pipeline works against a real database.
"""

from __future__ import annotations

import datetime as dt
import uuid

import pytest

pytest.importorskip("skimage")
pytest.importorskip("PIL")

from io import BytesIO  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

METHOD = "ISO_105_E04"  # seeded colour-fastness method (perspiration 37°C)
STRIP_PROFILE = "ISO_105_F10_DW"
FIBERS = ["diacetate", "cotton", "polyamide", "polyester", "acrylic", "wool"]


def _strip_png(colors, band_w=60, h=100):
    arr = np.zeros((h, band_w * len(colors), 3), dtype=np.uint8)
    for i, c in enumerate(colors):
        arr[:, i * band_w : (i + 1) * band_w] = c
    buf = BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


async def test_full_workflow_to_report(client, require_db):
    # ── 1. tenant bootstrap ────────────────────────────────────────────────
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"smoke-{uuid.uuid4().hex[:8]}@example.com",
            "password": "password123",
            "full_name": "Smoke Admin",
            "company_name": "Smoke Tessile SpA",
        },
    )
    assert reg.status_code == 201, reg.text
    tok = reg.json()
    assert tok["role"] == "company_admin"
    assert tok["company_id"]
    h = {"Authorization": f"Bearer {tok['access_token']}"}

    future = (dt.date.today() + dt.timedelta(days=365)).isoformat()

    # ── 2. brand specification + acceptance rule (pass/fail thresholds) ─────
    spec = await client.post(
        "/api/v1/brand-specifications",
        json={
            "brand_name": "Brand Z",
            "description": "Capitolato di esempio",
            "rules": [
                {
                    "test_method_code": METHOD,
                    "fiber_code": None,  # applies to every fibre
                    "max_delta_e": 3.0,
                    "min_gray_scale_grade": 3.0,
                    "severity": "blocking",
                }
            ],
        },
        headers=h,
    )
    assert spec.status_code == 201, spec.text
    spec_id = spec.json()["id"]
    assert len(spec.json()["rules"]) == 1

    # ── 3. article + production variant (reference Lab for colour-change) ───
    art = await client.post(
        "/api/v1/articles",
        json={"code": "ART-001", "name": "Jersey cotone", "composition": "100% CO"},
        headers=h,
    )
    assert art.status_code == 201, art.text
    article_id = art.json()["id"]

    var = await client.post(
        f"/api/v1/articles/{article_id}/variants",
        json={
            "code": "VAR-RED",
            "color_name": "Rosso",
            "lot_code": "L-2026-01",
            "reference_lab": {"L": 45.2, "a": 38.1, "b": 22.4},
        },
        headers=h,
    )
    assert var.status_code == 201, var.text
    variant_id = var.json()["id"]
    assert var.json()["reference_lab"]["L"] == 45.2

    # ── 4. multifibre batch zero (reference Lab per fibre) ──────────────────
    batch = await client.post(
        "/api/v1/multifiber-batches",
        json={
            "batch_code": "BZ-001",
            "strip_profile_code": STRIP_PROFILE,
            "reference_lab_values": {f: {"L": 96.0, "a": 0.0, "b": 0.0} for f in FIBERS},
        },
        headers=h,
    )
    assert batch.status_code == 201, batch.text
    batch_id = batch.json()["id"]

    # ── 5. calibration references (validity-tracked) ───────────────────────
    grey = await client.post(
        "/api/v1/calibration-references",
        json={
            "kind": "grey_scale",
            "code": "GS-A03",
            "subtype": "A03",
            "standard": "ISO 105-A03",
            "valid_until": future,
        },
        headers=h,
    )
    assert grey.status_code == 201, grey.text
    assert grey.json()["subtype"] == "A03"
    grey_id = grey.json()["id"]

    tile = await client.post(
        "/api/v1/calibration-references",
        json={
            "kind": "white_tile",
            "code": "WT-1",
            "reference_values": {"L": 95.1, "a": -0.2, "b": 1.1},
            "cert_illuminant": "D65",
            "cert_observer": "10",
            "valid_until": future,
        },
        headers=h,
    )
    assert tile.status_code == 201, tile.text
    tile_id = tile.json()["id"]

    blue = await client.post(
        "/api/v1/calibration-references",
        json={"kind": "blue_wool", "code": "BW-1", "series": "iso_1_8", "valid_until": future},
        headers=h,
    )
    assert blue.status_code == 201, blue.text
    assert blue.json()["series"] == "iso_1_8"

    lightbox = await client.post(
        "/api/v1/calibration-references",
        json={
            "kind": "lightbox",
            "code": "LB-1",
            "illuminants": ["D65"],
            "valid_until": future,
        },
        headers=h,
    )
    assert lightbox.status_code == 201, lightbox.text
    lightbox_id = lightbox.json()["id"]

    # ── 6. test job (linked to spec + method + article/variant) ────────────
    job = await client.post(
        "/api/v1/test-jobs",
        json={
            "brand_specification_id": spec_id,
            "test_method_code": METHOD,
            "article_code": "ART-001",
            "lot_code": "L-2026-01",
            "article_id": article_id,
            "article_variant_id": variant_id,
        },
        headers=h,
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]
    assert job.json()["status"] == "created"

    # ── 7. capture session + strip photo + Vision analysis (staining) ──────
    cs = await client.post(
        "/api/v1/capture-sessions",
        json={
            "test_job_id": job_id,
            "batch_id": batch_id,
            "test_method_code": METHOD,
            "capture_type": "multifiber_after",
            "lightbox_ref_id": lightbox_id,
            "grey_scale_ref_id": grey_id,
            "white_tile_ref_id": tile_id,
        },
        headers=h,
    )
    assert cs.status_code == 201, cs.text
    cs_id = cs.json()["id"]

    png = _strip_png([(245, 245, 245)] * len(FIBERS))  # clean strip
    img = await client.post(
        f"/api/v1/capture-sessions/{cs_id}/images?asset_type=multifiber_after",
        files={"file": ("strip.png", png, "image/png")},
        headers=h,
    )
    assert img.status_code == 201, img.text
    assert img.json()["sha256_hash"]

    analyze = await client.post(f"/api/v1/capture-sessions/{cs_id}/analyze", headers=h)
    assert analyze.status_code == 201, analyze.text
    res = analyze.json()["results"]
    assert res["source"] == "vision"
    assert res["assessment_type"] == "staining"
    assert set(res["vision"]["fibers"].keys()) == set(FIBERS)
    # linked references recorded in provenance and valid
    assert res["references"]["lightbox"]["code"] == "LB-1"
    assert res["references"]["grey_scale"]["code"] == "GS-A03"
    assert res["references"]["white_tile"]["validity"] in ("valid", "expiring")

    # ── 8. manual graded result (human verification) -> deterministic PASS ──
    manual = await client.post(
        f"/api/v1/test-jobs/{job_id}/manual-result",
        json={
            "test_method_code": METHOD,
            "fibers": {f: {"delta_e": 1.0, "gray_scale_grade": 4.5} for f in FIBERS},
            "notes": "Verificato dall'operatore",
        },
        headers=h,
    )
    assert manual.status_code == 201, manual.text
    pf = manual.json()["pass_fail"]
    assert pf["evaluated"] is True
    assert pf["overall_pass"] is True

    job_after = await client.get(f"/api/v1/test-jobs/{job_id}", headers=h)
    assert job_after.json()["status"] == "passed"

    # ── 9. generate report (number + SHA-256 integrity seal) ───────────────
    rep = await client.post(f"/api/v1/test-jobs/{job_id}/reports", headers=h)
    assert rep.status_code == 201, rep.text
    report = rep.json()
    report_id = report["id"]
    report_number = report["report_number"]
    sha = report["sha256_hash"]
    assert report["status"] == "generated"
    assert report_number.startswith("RPT-")
    assert len(sha) == 64

    # appears in the ledger
    ledger = await client.get("/api/v1/reports", headers=h)
    assert any(r["id"] == report_id for r in ledger.json())

    # ── 10. authenticated integrity verify -> valid ────────────────────────
    verify = await client.get(f"/api/v1/reports/{report_id}/verify", headers=h)
    assert verify.status_code == 200, verify.text
    assert verify.json()["valid"] is True
    assert verify.json()["recomputed_hash"] == sha

    # ── 11. finalize / lock (immutable) ────────────────────────────────────
    lock = await client.post(f"/api/v1/reports/{report_id}/finalize", headers=h)
    assert lock.status_code == 200, lock.text
    assert lock.json()["status"] == "locked"
    assert lock.json()["locked_at"]

    # ── 12. re-emission blocked once locked (409) ──────────────────────────
    reemit = await client.post(f"/api/v1/test-jobs/{job_id}/reports", headers=h)
    assert reemit.status_code == 409, reemit.text

    # ── 13. public verification (what the recipient checks via the QR) ─────
    pub_ok = await client.get(f"/api/v1/public/reports/{report_id}/verify?h={sha}")
    assert pub_ok.status_code == 200, pub_ok.text
    body = pub_ok.json()
    assert body["valid"] is True
    assert body["report_number"] == report_number
    assert body["locked"] is True

    pub_bad = await client.get(f"/api/v1/public/reports/{report_id}/verify?h=deadbeef")
    assert pub_bad.status_code == 200, pub_bad.text
    assert pub_bad.json()["valid"] is False

    # ── 14. PDF download (the final deliverable to send) ───────────────────
    pdf = await client.get(f"/api/v1/reports/{report_id}/download", headers=h)
    assert pdf.status_code == 200, pdf.text
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content[:4] == b"%PDF"
    assert len(pdf.content) > 500
