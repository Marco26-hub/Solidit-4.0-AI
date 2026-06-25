from __future__ import annotations

import uuid
from io import BytesIO

import pytest

pytest.importorskip("skimage")  # vision deps required for colour-change analyze
pytest.importorskip("PIL")

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402


def _solid_png(color: tuple[int, int, int], w: int = 80, h: int = 80) -> bytes:
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[:, :] = color
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


async def _colour_change_refs(client, h):
    import datetime as dt

    future = (dt.date.today() + dt.timedelta(days=365)).isoformat()
    lb = (
        await client.post(
            "/api/v1/calibration-references",
            json={"kind": "lightbox", "code": "LB-CC", "valid_until": future},
            headers=h,
        )
    ).json()
    wt = (
        await client.post(
            "/api/v1/calibration-references",
            json={
                "kind": "white_tile",
                "code": "WT-CC",
                "reference_values": {"L": 95.0, "a": 0.0, "b": 0.0},
                "valid_until": future,
            },
            headers=h,
        )
    ).json()
    return {"lightbox_ref_id": lb["id"], "white_tile_ref_id": wt["id"]}


async def test_grading_profiles_builtins_visible(client, require_db):
    reg = await _register(client, f"gp-{uuid.uuid4().hex[:8]}@example.com", "Grading Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    r = await client.get("/api/v1/articles/grading-profiles", headers=h)
    assert r.status_code == 200, r.text
    profiles = r.json()
    codes = {p["code"] for p in profiles}
    # builtin EXAMPLE profiles seeded by migration 0006
    assert "ISO_105_STAINING_EXAMPLE" in codes
    assert "AATCC_CHANGE_EXAMPLE" in codes
    assert all(p["is_builtin"] for p in profiles)

    # filter by family + type
    r = await client.get(
        "/api/v1/articles/grading-profiles",
        params={"standard_family": "AATCC", "assessment_type": "change"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    filtered = r.json()
    assert filtered and all(
        p["standard_family"] == "AATCC" and p["assessment_type"] == "change" for p in filtered
    )


async def test_article_with_variants_crud(client, require_db):
    reg = await _register(client, f"art-{uuid.uuid4().hex[:8]}@example.com", "Article Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    r = await client.post(
        "/api/v1/articles",
        json={
            "code": "ART-100",
            "name": "T-shirt jersey",
            "composition": "95% CO 5% EA",
            "variants": [
                {
                    "code": "RED",
                    "color_name": "Rosso",
                    "lot_code": "L1",
                    "reference_lab": {"L": 45.0, "a": 55.0, "b": 30.0},
                }
            ],
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    article = r.json()
    assert article["code"] == "ART-100"
    assert len(article["variants"]) == 1
    assert article["variants"][0]["code"] == "RED"

    # duplicate code rejected
    r = await client.post("/api/v1/articles", json={"code": "ART-100"}, headers=h)
    assert r.status_code == 409, r.text

    # add a second variant
    r = await client.post(
        f"/api/v1/articles/{article['id']}/variants",
        json={"code": "BLUE", "reference_lab": {"L": 40.0, "a": 5.0, "b": -45.0}},
        headers=h,
    )
    assert r.status_code == 201, r.text

    # list + get reflect both variants
    r = await client.get(f"/api/v1/articles/{article['id']}", headers=h)
    assert r.status_code == 200, r.text
    assert {v["code"] for v in r.json()["variants"]} == {"RED", "BLUE"}


async def test_colour_change_analyze_vs_variant_reference(client, require_db):
    reg = await _register(client, f"cc-{uuid.uuid4().hex[:8]}@example.com", "Colour Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    # article with a variant carrying the production-sample reference Lab
    ref_lab = {"L": 50.0, "a": 0.0, "b": 0.0}
    article = (
        await client.post(
            "/api/v1/articles",
            json={"code": "CC-1", "variants": [{"code": "GREY", "reference_lab": ref_lab}]},
            headers=h,
        )
    ).json()
    variant_id = article["variants"][0]["id"]

    job = (
        await client.post(
            "/api/v1/test-jobs",
            json={
                "test_method_code": "ISO_105_X12",
                "article_id": article["id"],
                "article_variant_id": variant_id,
            },
            headers=h,
        )
    ).json()
    assert job["article_variant_id"] == variant_id

    cs = (
        await client.post(
            "/api/v1/capture-sessions",
            json={
                "test_job_id": job["id"],
                "test_method_code": "ISO_105_X12",
                "capture_type": "colour_change",
                **await _colour_change_refs(client, h),
            },
            headers=h,
        )
    ).json()

    # a clearly different fabric colour (strong red) vs grey reference -> large ΔE
    png = _solid_png((200, 30, 30))
    r = await client.post(
        f"/api/v1/capture-sessions/{cs['id']}/images?asset_type=fabric_after",
        files={"file": ("fabric.png", png, "image/png")},
        headers=h,
    )
    assert r.status_code == 201, r.text

    r = await client.post(f"/api/v1/capture-sessions/{cs['id']}/analyze", headers=h)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["results"]["assessment_type"] == "change"
    vis = body["results"]["vision"]
    assert vis["delta_e"] > 10  # big colour difference
    assert 1.0 <= vis["gray_scale_grade"] <= 5.0
