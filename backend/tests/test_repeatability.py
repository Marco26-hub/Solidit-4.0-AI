from __future__ import annotations

import uuid
from io import BytesIO

import pytest

pytest.importorskip("skimage")
pytest.importorskip("PIL")

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402


def _strip_png(stain_rgb):
    cols = [(245, 245, 245)] * 5 + [stain_rgb]
    arr = np.zeros((100, 60 * 6, 3), dtype=np.uint8)
    for i, c in enumerate(cols):
        arr[:, i * 60 : (i + 1) * 60] = c
    buf = BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


async def _register(client, email, company):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _hardware_refs(client, h, suffix: str):
    import datetime as dt

    future = (dt.date.today() + dt.timedelta(days=365)).isoformat()
    lb = (
        await client.post(
            "/api/v1/calibration-references",
            json={"kind": "lightbox", "code": f"LB-{suffix}", "valid_until": future},
            headers=h,
        )
    ).json()
    gs = (
        await client.post(
            "/api/v1/calibration-references",
            json={"kind": "grey_scale", "code": f"GS-{suffix}", "valid_until": future},
            headers=h,
        )
    ).json()
    wt = (
        await client.post(
            "/api/v1/calibration-references",
            json={
                "kind": "white_tile",
                "code": f"WT-{suffix}",
                "reference_values": {"L": 95.0, "a": 0.0, "b": 0.0},
                "valid_until": future,
            },
            headers=h,
        )
    ).json()
    return {
        "lightbox_ref_id": lb["id"],
        "grey_scale_ref_id": gs["id"],
        "white_tile_ref_id": wt["id"],
    }


async def test_repeatability_aggregates_replicates(client, require_db):
    reg = await _register(client, f"rep-{uuid.uuid4().hex[:8]}@example.com", "Rep Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    fibers = ["diacetate", "cotton", "polyamide", "polyester", "acrylic", "wool"]
    ref = {f: {"L": 96.0, "a": 0.0, "b": 0.0} for f in fibers}
    batch = (
        await client.post(
            "/api/v1/multifiber-batches",
            json={
                "batch_code": "MF-R",
                "strip_profile_code": "ISO_105_F10_DW",
                "reference_lab_values": ref,
            },
            headers=h,
        )
    ).json()
    job = (
        await client.post("/api/v1/test-jobs", json={"test_method_code": "ISO_105_E04"}, headers=h)
    ).json()
    cs = (
        await client.post(
            "/api/v1/capture-sessions",
            json={
                "test_job_id": job["id"],
                "batch_id": batch["id"],
                "test_method_code": "ISO_105_E04",
                "capture_type": "multifiber_after",
                **await _hardware_refs(client, h, "R"),
            },
            headers=h,
        )
    ).json()

    # 3 replicate photos with slightly different stain intensity on the wool band
    for stain in [(170, 80, 80), (175, 82, 82), (168, 78, 78)]:
        r = await client.post(
            f"/api/v1/capture-sessions/{cs['id']}/images?asset_type=multifiber_after",
            files={"file": ("s.png", _strip_png(stain), "image/png")},
            headers=h,
        )
        assert r.status_code == 201, r.text

    body = (
        await client.post(f"/api/v1/capture-sessions/{cs['id']}/analyze", headers=h)
    ).json()
    rep = body["results"]["vision"]["repeatability"]
    assert rep["replicates"] == 3
    assert "wool" in rep["per_fiber"]
    assert rep["per_fiber"]["wool"]["mean_delta_e"] > 10
    assert len(rep["per_fiber"]["wool"]["replicate_grades"]) == 3
    assert rep["max_deviation_grade"] >= 0.0


async def test_strict_quality_rejects_poor_capture(client, require_db):
    reg = await _register(client, f"str-{uuid.uuid4().hex[:8]}@example.com", "Strict Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    fibers = ["diacetate", "cotton", "polyamide", "polyester", "acrylic", "wool"]
    ref = {f: {"L": 96.0, "a": 0.0, "b": 0.0} for f in fibers}
    batch = (
        await client.post(
            "/api/v1/multifiber-batches",
            json={
                "batch_code": "MF-S",
                "strip_profile_code": "ISO_105_F10_DW",
                "reference_lab_values": ref,
            },
            headers=h,
        )
    ).json()
    job = (
        await client.post("/api/v1/test-jobs", json={"test_method_code": "ISO_105_E04"}, headers=h)
    ).json()
    cs = (
        await client.post(
            "/api/v1/capture-sessions",
            json={
                "test_job_id": job["id"],
                "batch_id": batch["id"],
                "test_method_code": "ISO_105_E04",
                "capture_type": "multifiber_after",
                "strict_quality": True,
                **await _hardware_refs(client, h, "S"),
            },
            headers=h,
        )
    ).json()
    await client.post(
        f"/api/v1/capture-sessions/{cs['id']}/images?asset_type=multifiber_after",
        files={"file": ("s.png", _strip_png((170, 80, 80)), "image/png")},
        headers=h,
    )
    # synthetic flat strip trips blur/exposure -> strict mode blocks
    r = await client.post(f"/api/v1/capture-sessions/{cs['id']}/analyze", headers=h)
    assert r.status_code == 400, r.text
    assert "capture_rejected" in r.text or "rifiutata" in r.text.lower()
