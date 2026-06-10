from __future__ import annotations

import uuid
from io import BytesIO

import pytest

pytest.importorskip("skimage")  # vision deps required for this module
pytest.importorskip("PIL")

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from app.vision.delta_e import compute_delta_e_ciede2000  # noqa: E402
from app.vision.pipeline import analyze_multifiber  # noqa: E402


def _strip_png(colors: list[tuple[int, int, int]], band_w: int = 60, h: int = 100) -> bytes:
    arr = np.zeros((h, band_w * len(colors), 3), dtype=np.uint8)
    for i, c in enumerate(colors):
        arr[:, i * band_w : (i + 1) * band_w] = c
    buf = BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


# ── pure engine ─────────────────────────────────────────────────────────────
def test_delta_e_identical_is_zero():
    assert compute_delta_e_ciede2000([50, 0, 0], [50, 0, 0]) == pytest.approx(0.0, abs=1e-6)


def test_delta_e_positive_for_difference():
    assert compute_delta_e_ciede2000([50, 0, 0], [60, 5, -5]) > 1.0


def test_analyze_grades_clean_vs_stained():
    fibers = ["cotton", "wool", "nylon"]
    reference = {f: {"L": 96.0, "a": 0.0, "b": 0.0} for f in fibers}
    # cotton near-white (clean), wool near-white, nylon strongly stained (red)
    png = _strip_png([(245, 245, 245), (243, 244, 245), (180, 90, 90)])
    result = analyze_multifiber(png, fibers, reference)
    assert result["algorithm_version"].startswith("vision-core")
    f = result["fibers"]
    assert set(f) == set(fibers)
    # the stained band has a much larger ΔE and a lower (worse) grade than a clean one
    assert f["nylon"]["delta_e"] > f["cotton"]["delta_e"]
    assert f["nylon"]["gray_scale_grade"] <= f["cotton"]["gray_scale_grade"]


# ── full capture -> upload -> analyze (DB) ──────────────────────────────────────
async def _register(client, email, company):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_vision_analyze_flow(client, require_db):
    reg = await _register(client, f"vis-{uuid.uuid4().hex[:8]}@example.com", "Vision Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    fibers = ["diacetate", "cotton", "polyamide", "polyester", "acrylic", "wool"]
    ref = {f: {"L": 96.0, "a": 0.0, "b": 0.0} for f in fibers}
    batch = (
        await client.post(
            "/api/v1/multifiber-batches",
            json={
                "batch_code": "MF-VIS",
                "strip_profile_code": "ISO_105_F10_DW",
                "reference_lab_values": ref,
            },
            headers=h,
        )
    ).json()
    assert batch["strip_profile_code"] == "ISO_105_F10_DW"

    job = (
        await client.post(
            "/api/v1/test-jobs",
            json={"test_method_code": "ISO_105_X12", "article_code": "A1"},
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
            },
            headers=h,
        )
    ).json()

    png = _strip_png([(245, 245, 245)] * 5 + [(170, 80, 80)])  # wool band stained
    r = await client.post(
        f"/api/v1/capture-sessions/{cs['id']}/images?asset_type=multifiber_after",
        files={"file": ("strip.png", png, "image/png")},
        headers=h,
    )
    assert r.status_code == 201, r.text

    r = await client.post(f"/api/v1/capture-sessions/{cs['id']}/analyze", headers=h)
    assert r.status_code == 201, r.text
    body = r.json()
    vis = body["results"]["vision"]["fibers"]
    assert "wool" in vis and "cotton" in vis
    assert vis["wool"]["delta_e"] > vis["cotton"]["delta_e"]
    assert "overall_pass" in body["pass_fail"]
