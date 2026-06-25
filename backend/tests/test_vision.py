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


def _aruco_frame(
    colors: list[tuple[int, int, int]], w: int = 800, h: int = 500, marker: int = 90
) -> bytes:
    """White canvas with the four dima ArUco fiducials (ids 0/1/2/3 at
    TL/TR/BR/BL) and the multifibre strip drawn inside the marker quad."""
    cv2 = pytest.importorskip("cv2")
    canvas = np.full((h, w, 3), 255, np.uint8)
    dic = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    pad = 10
    spots = {  # id -> top-left pixel of the marker
        0: (pad, pad),
        1: (w - marker - pad, pad),
        2: (w - marker - pad, h - marker - pad),
        3: (pad, h - marker - pad),
    }
    for mid, (x, y) in spots.items():
        img = cv2.aruco.generateImageMarker(dic, mid, marker)
        canvas[y : y + marker, x : x + marker] = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    # strip across the inner region between the markers
    sx0, sx1 = marker + 2 * pad, w - marker - 2 * pad
    sy0, sy1 = marker + 2 * pad, h - marker - 2 * pad
    band_w = (sx1 - sx0) // len(colors)
    for i, c in enumerate(colors):
        canvas[sy0:sy1, sx0 + i * band_w : sx0 + (i + 1) * band_w] = c
    buf = BytesIO()
    Image.fromarray(canvas).save(buf, format="PNG")
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


# ── ArUco markers + homography (geometry, separate from colour) ──────────────
def test_detect_markers_finds_dima_corners():
    pytest.importorskip("cv2")
    from app.vision.markers import CORNER_IDS, detect_markers

    png = _aruco_frame([(245, 245, 245), (180, 90, 90), (90, 90, 180)])
    arr = np.array(Image.open(BytesIO(png)).convert("RGB"))
    m = detect_markers(arr)
    assert m["found"] == 4
    assert m["has_corner_quad"] is True
    assert all(cid in m["centers"] for cid in CORNER_IDS)


def test_rectify_perspective_warps_to_canvas():
    pytest.importorskip("cv2")
    from app.vision.geometry import rectify_perspective
    from app.vision.markers import detect_markers

    png = _aruco_frame([(245, 245, 245), (180, 90, 90), (90, 90, 180)])
    arr = np.array(Image.open(BytesIO(png)).convert("RGB"))
    rect = rectify_perspective(arr, detect_markers(arr), output_size=(600, 400))
    assert rect["applied"] is True
    assert rect["method"] == "homography_aruco"
    assert rect["image"].shape == (400, 600, 3)


def test_rectify_skipped_without_markers():
    from app.vision.geometry import rectify_perspective
    from app.vision.markers import detect_markers

    plain = _strip_png([(245, 245, 245), (180, 90, 90)])
    arr = np.array(Image.open(BytesIO(plain)).convert("RGB"))
    rect = rectify_perspective(arr, detect_markers(arr))
    assert rect["applied"] is False
    assert rect["image"] is None


def test_pipeline_geometry_markers_rectifies():
    pytest.importorskip("cv2")
    fibers = ["cotton", "wool", "nylon"]
    reference = {f: {"L": 96.0, "a": 0.0, "b": 0.0} for f in fibers}
    png = _aruco_frame([(245, 245, 245), (243, 244, 245), (180, 90, 90)])
    result = analyze_multifiber(png, fibers, reference, geometry_markers=True)
    geo = result["quality_flags"]["geometry"]
    assert geo["requested"] is True
    assert geo["rectified"] is True
    assert geo["method"] == "homography_aruco"
    assert result["fibers"]["nylon"]["delta_e"] > result["fibers"]["cotton"]["delta_e"]


def test_pipeline_geometry_markers_fallback_flagged():
    # markers requested but absent -> flagged fallback, analysis still runs
    fibers = ["cotton", "wool", "nylon"]
    reference = {f: {"L": 96.0, "a": 0.0, "b": 0.0} for f in fibers}
    png = _strip_png([(245, 245, 245), (243, 244, 245), (180, 90, 90)])
    result = analyze_multifiber(png, fibers, reference, geometry_markers=True)
    geo = result["quality_flags"]["geometry"]
    assert geo["requested"] is True
    assert geo["rectified"] is False
    assert any("geometry: marker ArUco" in w for w in result["warnings"])


# ── full capture -> upload -> analyze (DB) ──────────────────────────────────────
async def _register(client, email, company):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _hardware_refs(client, h):
    import datetime as dt

    future = (dt.date.today() + dt.timedelta(days=365)).isoformat()
    lb = (
        await client.post(
            "/api/v1/calibration-references",
            json={"kind": "lightbox", "code": "LB-VIS", "valid_until": future},
            headers=h,
        )
    ).json()
    gs = (
        await client.post(
            "/api/v1/calibration-references",
            json={"kind": "grey_scale", "code": "GS-VIS", "valid_until": future},
            headers=h,
        )
    ).json()
    wt = (
        await client.post(
            "/api/v1/calibration-references",
            json={
                "kind": "white_tile",
                "code": "WT-VIS",
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
                **await _hardware_refs(client, h),
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
