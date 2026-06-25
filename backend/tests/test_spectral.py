from __future__ import annotations

import uuid

import pytest

pytest.importorskip("numpy")

from app.config import settings  # noqa: E402
from app.vision.spectral import (  # noqa: E402
    N_BANDS,
    estimate_reflectance,
    render_under_illuminant,
    white_point,
)


# ── pure engine ──────────────────────────────────────────────────────────────
def test_d65_white_point_matches_reference():
    # canonical CIE D65 2° white point ≈ [95.047, 100.0, 108.883]; 10 nm tables
    # land within ~0.5 — this guards the embedded CMF/D65 transcription.
    x, y, z = white_point("D65")
    assert y == pytest.approx(100.0, abs=1e-6)
    assert x == pytest.approx(95.047, abs=0.5)
    assert z == pytest.approx(108.883, abs=0.5)


def test_estimate_returns_valid_reflectance():
    est = estimate_reflectance([55.0, 20.0, -15.0])
    assert est["estimate"] is True
    assert est["not_a_measurement"] is True
    assert est["label"] == "STIMATA"
    assert len(est["reflectance"]) == N_BANDS == 31
    assert all(0.0 <= v <= 1.0 for v in est["reflectance"])
    assert len(est["wavelengths_nm"]) == 31
    assert "disclaimer" in est and "STIMATA" in est["disclaimer"]


def test_estimate_is_colour_faithful_roundtrip():
    # LHTSS reproduces the measured colour essentially exactly (round-trip ΔE ≈ 0)
    for lab in ([60, 0, 0], [50, 40, 30], [30, 10, -25], [70, -30, 20]):
        est = estimate_reflectance(lab)
        assert est["roundtrip_delta_e"] < 0.2
        assert est["confidence"] > 0.9


def test_lhtss_reflectance_strictly_in_open_unit_interval():
    # ρ = (tanh z + 1)/2 ∈ (0,1) for all z — bounds are built in, never clipped
    est = estimate_reflectance([45, 60, 35])
    assert all(0.0 < v < 1.0 for v in est["reflectance"])


def test_rgb_to_reflectance_saturated_red_is_exact():
    # the old clip method distorted saturated reds (ΔE ~3.8); LHTSS reproduces it
    from app.vision.spectral import reflectance_from_rgb

    est = reflectance_from_rgb([200, 30, 40])
    assert est["engine"] == "lhtss"
    assert est["in_gamut"] is True
    assert est["roundtrip_delta_e"] < 0.5
    assert est["input_rgb"] == [200, 30, 40]
    assert len(est["reflectance"]) == 31


def test_rgb_white_maps_to_canonical_d65_white():
    from app.vision.spectral import _srgb_to_xyz

    xyz = _srgb_to_xyz([255, 255, 255])
    assert float(xyz[0]) == pytest.approx(95.047, abs=0.05)
    assert float(xyz[1]) == pytest.approx(100.0, abs=0.05)
    assert float(xyz[2]) == pytest.approx(108.883, abs=0.05)


def test_estimate_is_deterministic():
    a = estimate_reflectance([50, 12, -8])
    b = estimate_reflectance([50, 12, -8])
    assert a["reflectance"] == b["reflectance"]


def test_render_under_same_illuminant_is_identity():
    lab = [48.0, 25.0, 12.0]
    est = estimate_reflectance(lab, illuminant="D65")
    back = render_under_illuminant(est["reflectance"], "D65")
    assert back["lab"][0] == pytest.approx(lab[0], abs=0.5)
    assert back["lab"][1] == pytest.approx(lab[1], abs=0.5)
    assert back["lab"][2] == pytest.approx(lab[2], abs=0.5)


def test_render_under_illuminant_a_shifts_colour():
    est = estimate_reflectance([50, 40, 30], illuminant="D65")
    under_a = render_under_illuminant(est["reflectance"], "A")
    under_d65 = render_under_illuminant(est["reflectance"], "D65")
    assert under_a["lab"] != under_d65["lab"]  # incandescent A warms the colour
    assert all(0 <= c <= 255 for c in under_a["srgb"])


def test_metamerism_differing_samples_under_test_light():
    from app.vision.spectral import metamerism_pair

    m = metamerism_pair([45, 60, 35], [45, 55, 48])
    assert m["label"] == "STIMATA"
    assert m["not_a_measurement"] is True
    assert m["delta_e_reference"] > 1.0
    assert len(m["per_illuminant"]) == 1
    row = m["per_illuminant"][0]
    assert row["illuminant"] == "A"
    assert "metamerism_index" in row and row["metamerism_index"] >= 0.0
    assert m["warnings"] == []  # they differ under D65 → no "collapse" caveat


def test_metamerism_matched_samples_flag_limitation():
    # rule 7: samples matching under the reference illuminant collapse to the same
    # ESTIMATED spectrum → MI≈0 and the hard limitation must be flagged loudly.
    from app.vision.spectral import metamerism_pair

    m = metamerism_pair([50, 20, 10], [50, 20, 10])
    assert m["delta_e_reference"] == pytest.approx(0.0, abs=1e-6)
    assert m["per_illuminant"][0]["metamerism_index"] == pytest.approx(0.0, abs=1e-6)
    assert any("metamerismo reale" in w for w in m["warnings"])


def test_unsupported_illuminant_rejected():
    from app.common.errors import AppError
    from app.spectral.service import estimate_lab

    with pytest.raises(AppError):
        estimate_lab([50, 0, 0], illuminant="F11")


# ── pluggable backend ────────────────────────────────────────────────────────
def test_default_backend_is_smoothest():
    from app.spectral.service import get_estimator

    estimator, fallback = get_estimator()
    assert estimator.name == "smoothest"
    assert fallback is None


def test_remote_ml_without_url_falls_back(monkeypatch):
    from app.spectral.service import get_estimator

    monkeypatch.setattr(settings, "spectral_backend", "remote_ml")
    monkeypatch.setattr(settings, "spectral_inference_url", None)
    estimator, fallback = get_estimator()
    assert estimator.name == "smoothest"
    assert fallback and "SPECTRAL_INFERENCE_URL" in fallback


def test_remote_ml_forces_honesty_fields(monkeypatch):
    # rule 7: an UNTRUSTED remote model must never be able to relabel an estimate
    # as a measurement, nor swap the disclaimer. The backend overwrites them.
    import httpx

    from app.spectral.service import RemoteMLEstimator
    from app.vision.spectral import DISCLAIMER, WAVELENGTHS

    class _Resp:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {
                "label": "Misura accreditata",
                "engine": "spettrofotometro",
                "disclaimer": "Spettro misurato in laboratorio accreditato",
                "estimate": False,
                "not_a_measurement": False,
                "method": "remote-net",
                "illuminant": "D65",
                "observer": "2",
                "wavelengths_nm": list(WAVELENGTHS),
                "reflectance": [0.5] * 31,
                "input_lab": [50.0, 0.0, 0.0],
                "roundtrip_lab": [50.0, 0.0, 0.0],
                "roundtrip_delta_e": 0.0,
                "confidence": 0.99,
                "warnings": [],
            }

    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Resp())
    out = RemoteMLEstimator("http://spark.local").estimate(
        [50.0, 0.0, 0.0], illuminant="D65", observer="2"
    )
    assert out["label"] == "STIMATA"
    assert out["engine"] == "remote_ml"
    assert out["estimate"] is True
    assert out["not_a_measurement"] is True
    assert out["disclaimer"] == DISCLAIMER


# ── API ──────────────────────────────────────────────────────────────────────
async def _register(client, email, company):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_estimate_endpoint_requires_auth(client, require_db):
    r = await client.post("/api/v1/spectral/estimate", json={"lab": {"L": 50, "a": 0, "b": 0}})
    assert r.status_code == 401


async def test_estimate_endpoint_returns_stimata(client, require_db):
    reg = await _register(client, f"sp-{uuid.uuid4().hex[:8]}@example.com", "Spectral Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    r = await client.post(
        "/api/v1/spectral/estimate",
        json={"lab": {"L": 55, "a": 20, "b": -10}, "illuminant": "D65"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["label"] == "STIMATA"
    assert body["not_a_measurement"] is True
    assert len(body["reflectance"]) == 31
    assert body["illuminant"] == "D65"


async def test_estimate_rgb_endpoint(client, require_db):
    reg = await _register(client, f"rgb-{uuid.uuid4().hex[:8]}@example.com", "Rgb Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    r = await client.post(
        "/api/v1/spectral/estimate-rgb",
        json={"rgb": {"r": 200, "g": 30, "b": 40}},
        headers=h,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["label"] == "STIMATA"
    assert body["engine"] == "lhtss"
    assert body["illuminant"] == "D65"
    assert body["in_gamut"] is True
    assert len(body["reflectance"]) == 31
    assert body["input_rgb"] == [200, 30, 40]


async def test_metamerism_endpoint(client, require_db):
    reg = await _register(client, f"mt-{uuid.uuid4().hex[:8]}@example.com", "Metam Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    r = await client.post(
        "/api/v1/spectral/metamerism",
        json={
            "lab_reference": {"L": 45, "a": 60, "b": 35},
            "lab_sample": {"L": 45, "a": 55, "b": 48},
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["label"] == "STIMATA"
    assert body["not_a_measurement"] is True
    assert body["per_illuminant"][0]["illuminant"] == "A"


async def test_spectral_estimate_not_written_into_report_payload(client, require_db):
    # rule 7: the estimated spectrum must never leak into the accredited result/report
    reg = await _register(client, f"sp2-{uuid.uuid4().hex[:8]}@example.com", "Spectral Co2")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    fibers = ["cotton", "wool"]
    ref = {f: {"L": 96.0, "a": 0.0, "b": 0.0} for f in fibers}
    batch = (
        await client.post(
            "/api/v1/multifiber-batches",
            json={
                "batch_code": "MF-SP",
                "strip_profile_code": "ISO_105_F10_DW",
                "reference_lab_values": ref,
            },
            headers=h,
        )
    ).json()
    job = (
        await client.post(
            "/api/v1/test-jobs",
            json={"test_method_code": "ISO_105_X12", "article_code": "A1"},
            headers=h,
        )
    ).json()
    import datetime as dt

    future = (dt.date.today() + dt.timedelta(days=365)).isoformat()
    lb = (
        await client.post(
            "/api/v1/calibration-references",
            json={"kind": "lightbox", "code": "LB-SP", "valid_until": future},
            headers=h,
        )
    ).json()
    gs = (
        await client.post(
            "/api/v1/calibration-references",
            json={"kind": "grey_scale", "code": "GS-SP", "valid_until": future},
            headers=h,
        )
    ).json()
    wt = (
        await client.post(
            "/api/v1/calibration-references",
            json={
                "kind": "white_tile",
                "code": "WT-SP",
                "reference_values": {"L": 95.0, "a": 0.0, "b": 0.0},
                "valid_until": future,
            },
            headers=h,
        )
    ).json()
    cs = (
        await client.post(
            "/api/v1/capture-sessions",
            json={
                "test_job_id": job["id"],
                "batch_id": batch["id"],
                "test_method_code": "ISO_105_X12",
                "capture_type": "multifiber_after",
                "lightbox_ref_id": lb["id"],
                "grey_scale_ref_id": gs["id"],
                "white_tile_ref_id": wt["id"],
            },
            headers=h,
        )
    ).json()
    import io

    import numpy as np
    from PIL import Image

    arr = np.zeros((100, 120, 3), dtype=np.uint8)
    arr[:, :60] = (245, 245, 245)
    arr[:, 60:] = (170, 80, 80)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    await client.post(
        f"/api/v1/capture-sessions/{cs['id']}/images?asset_type=multifiber_after",
        files={"file": ("strip.png", buf.getvalue(), "image/png")},
        headers=h,
    )
    res = (await client.post(f"/api/v1/capture-sessions/{cs['id']}/analyze", headers=h)).json()

    # the stored measurement result carries NO reflectance/spectral payload
    import json as _json

    blob = _json.dumps(res)
    assert "reflectance" not in blob
    assert "wavelengths_nm" not in blob

    # but the spectral endpoint can estimate per fibre on demand (separate path)
    sp = await client.get(
        f"/api/v1/spectral/measurement-results/{res['id']}", headers=h
    )
    assert sp.status_code == 200, sp.text
    spb = sp.json()
    assert spb["label"] == "STIMATA"
    assert len(spb["fibers"]) >= 1
    assert all(len(f["estimate"]["reflectance"]) == 31 for f in spb["fibers"])
