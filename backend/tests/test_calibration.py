from __future__ import annotations

import datetime as dt
import uuid

import pytest

pytest.importorskip("skimage")
pytest.importorskip("PIL")

from io import BytesIO  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402


def _strip_png(colors, band_w=60, h=100):
    arr = np.zeros((h, band_w * len(colors), 3), dtype=np.uint8)
    for i, c in enumerate(colors):
        arr[:, i * band_w : (i + 1) * band_w] = c
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


async def _setup_staining(client, h, *, refs=None):
    fibers = ["diacetate", "cotton", "polyamide", "polyester", "acrylic", "wool"]
    ref = {f: {"L": 96.0, "a": 0.0, "b": 0.0} for f in fibers}
    batch = (
        await client.post(
            "/api/v1/multifiber-batches",
            json={
                "batch_code": "MF",
                "strip_profile_code": "ISO_105_F10_DW",
                "reference_lab_values": ref,
            },
            headers=h,
        )
    ).json()
    job = (
        await client.post("/api/v1/test-jobs", json={"test_method_code": "ISO_105_E04"}, headers=h)
    ).json()
    body = {
        "test_job_id": job["id"],
        "batch_id": batch["id"],
        "test_method_code": "ISO_105_E04",
        "capture_type": "multifiber_after",
    }
    if refs:
        body.update(refs)
    cs = (await client.post("/api/v1/capture-sessions", json=body, headers=h)).json()
    png = _strip_png([(245, 245, 245)] * 5 + [(170, 80, 80)])
    await client.post(
        f"/api/v1/capture-sessions/{cs['id']}/images?asset_type=multifiber_after",
        files={"file": ("s.png", png, "image/png")},
        headers=h,
    )
    return cs


async def test_reference_crud_and_validity(client, require_db):
    reg = await _register(client, f"cal-{uuid.uuid4().hex[:8]}@example.com", "Cal Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    future = (dt.date.today() + dt.timedelta(days=365)).isoformat()
    r = await client.post(
        "/api/v1/calibration-references",
        json={
            "kind": "grey_scale",
            "code": "GS-1",
            "certificate_number": "C123",
            "valid_until": future,
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    assert r.json()["validity"] == "valid"

    lst = (await client.get("/api/v1/calibration-references", headers=h)).json()
    assert any(x["code"] == "GS-1" for x in lst)


async def test_expired_reference_blocks_analyze(client, require_db):
    reg = await _register(client, f"exp-{uuid.uuid4().hex[:8]}@example.com", "Exp Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    past = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    gs = (
        await client.post(
            "/api/v1/calibration-references",
            json={"kind": "grey_scale", "code": "GS-OLD", "valid_until": past},
            headers=h,
        )
    ).json()
    assert gs["validity"] == "expired"

    cs = await _setup_staining(client, h, refs={"grey_scale_ref_id": gs["id"]})
    r = await client.post(f"/api/v1/capture-sessions/{cs['id']}/analyze", headers=h)
    assert r.status_code == 400, r.text
    assert "scadut" in r.text.lower() or "reference_invalid" in r.text


async def test_valid_reference_allows_analyze_with_provenance(client, require_db):
    reg = await _register(client, f"val-{uuid.uuid4().hex[:8]}@example.com", "Val Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    future = (dt.date.today() + dt.timedelta(days=200)).isoformat()
    gs = (
        await client.post(
            "/api/v1/calibration-references",
            json={"kind": "grey_scale", "code": "GS-OK", "valid_until": future},
            headers=h,
        )
    ).json()

    cs = await _setup_staining(client, h, refs={"grey_scale_ref_id": gs["id"]})
    r = await client.post(f"/api/v1/capture-sessions/{cs['id']}/analyze", headers=h)
    assert r.status_code == 201, r.text
    body = r.json()
    prov = body["results"]["references"]
    assert prov["grey_scale"]["code"] == "GS-OK"
    assert prov["grey_scale"]["validity"] in ("valid", "expiring")


async def test_analyze_without_references_warns_not_blocks(client, require_db):
    reg = await _register(client, f"now-{uuid.uuid4().hex[:8]}@example.com", "NoRef Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    cs = await _setup_staining(client, h)
    r = await client.post(f"/api/v1/capture-sessions/{cs['id']}/analyze", headers=h)
    assert r.status_code == 201, r.text
    warnings = r.json()["results"]["vision"]["warnings"]
    assert any("riferimento" in w or "accreditabile" in w for w in warnings)


async def test_blue_wool_reference_and_meta_roundtrip(client, require_db):
    reg = await _register(client, f"bw-{uuid.uuid4().hex[:8]}@example.com", "BlueWool Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    r = await client.post(
        "/api/v1/calibration-references",
        json={
            "kind": "blue_wool",
            "code": "BW-1",
            "series": "iso_1_8",
            "standard": "ISO 105-B02",
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["validity"] == "valid"
    assert body["series"] == "iso_1_8"
    assert body["standard"] == "ISO 105-B02"

    lst = (await client.get("/api/v1/calibration-references", headers=h)).json()
    bw = next(x for x in lst if x["code"] == "BW-1")
    assert bw["kind"] == "blue_wool"
    assert bw["series"] == "iso_1_8"


async def test_grey_scale_subtype_roundtrip(client, require_db):
    reg = await _register(client, f"gs-{uuid.uuid4().hex[:8]}@example.com", "Grey Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    for code, subtype, std in [("GS-A03", "A03", "ISO 105-A03"), ("GS-A02", "A02", "ISO 105-A02")]:
        r = await client.post(
            "/api/v1/calibration-references",
            json={"kind": "grey_scale", "code": code, "subtype": subtype, "standard": std},
            headers=h,
        )
        assert r.status_code == 201, r.text
        assert r.json()["subtype"] == subtype

    lst = (await client.get("/api/v1/calibration-references", headers=h)).json()
    subtypes = {x["code"]: x["subtype"] for x in lst if x["kind"] == "grey_scale"}
    assert subtypes == {"GS-A03": "A03", "GS-A02": "A02"}


async def test_lightbox_illuminants_and_white_tile_cert_obs(client, require_db):
    reg = await _register(client, f"lb-{uuid.uuid4().hex[:8]}@example.com", "Light Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    lb = await client.post(
        "/api/v1/calibration-references",
        json={"kind": "lightbox", "code": "LB-1", "illuminants": ["D65", "TL84"], "lamp_hours": 120},
        headers=h,
    )
    assert lb.status_code == 201, lb.text
    assert lb.json()["illuminants"] == ["D65", "TL84"]

    wt = await client.post(
        "/api/v1/calibration-references",
        json={
            "kind": "white_tile",
            "code": "WT-1",
            "reference_values": {"L": 95.1, "a": -0.2, "b": 1.1},
            "cert_illuminant": "D65",
            "cert_observer": "10",
        },
        headers=h,
    )
    assert wt.status_code == 201, wt.text
    assert wt.json()["cert_illuminant"] == "D65"
    assert wt.json()["reference_values"] == {"L": 95.1, "a": -0.2, "b": 1.1}
