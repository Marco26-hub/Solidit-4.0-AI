from __future__ import annotations

import uuid

import pytest

pytest.importorskip("numpy")

import numpy as np  # noqa: E402

from app.vision.characterization import (  # noqa: E402
    COLORCHECKER_LAB,
    colorchecker_xyz,
    fit_camera_transform,
)
from app.vision.uncertainty import combine_uncertainty  # noqa: E402

# sRGB linear→XYZ matrix (D65); its inverse builds an ideal linear camera.
_M = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ]
)


def _ideal_linear_camera() -> list[list[float]]:
    xyz = np.array(colorchecker_xyz())
    lin = np.clip((np.linalg.inv(_M) @ (xyz / 100.0).T).T, 0.0, 1.0)
    return lin.tolist()


# ── characterisation engine ──────────────────────────────────────────────────
def test_colorchecker_reference_sane():
    assert len(COLORCHECKER_LAB) == 24
    white = COLORCHECKER_LAB[18]  # patch 19 = white
    black = COLORCHECKER_LAB[23]  # patch 24 = black
    assert white[0] > 90 and black[0] < 25


def test_characterization_recovers_ideal_linear_camera():
    # an ideal linear sRGB camera → degree-3 root-poly should be near-exact
    cam = _ideal_linear_camera()
    fit = fit_camera_transform(cam, degree=3)
    assert fit["method"] == "root_polynomial"
    assert fit["n_terms"] == 13
    assert fit["residual"]["mean_delta_e"] < 0.2
    assert fit["residual"]["max_delta_e"] < 1.0


def test_characterization_corrects_distorted_sensor():
    # crosstalk + channel gain + noise → still colorimeter-grade after fit
    cam = np.array(_ideal_linear_camera())
    crosstalk = np.array([[1.0, 0.07, 0.02], [0.05, 1.0, 0.04], [0.02, 0.06, 1.0]])
    cam = np.clip((crosstalk @ cam.T).T * np.array([1.04, 0.98, 0.95]), 0.0, 1.0)
    fit = fit_camera_transform(cam.tolist(), degree=3)
    assert fit["residual"]["mean_delta_e"] < 2.0  # << raw-sRGB error (~5-9 ΔE)


def test_characterization_rejects_too_few_patches():
    from app.colorimetry.service import characterize
    from app.common.errors import AppError

    with pytest.raises(AppError):
        characterize([[0.1, 0.1, 0.1]], degree=2)  # 1 patch < 6 terms


# ── uncertainty budget ───────────────────────────────────────────────────────
def test_uncertainty_combines_in_quadrature():
    out = combine_uncertainty({"repeatability": 0.3, "characterisation": 0.4})
    # sqrt(0.09+0.16)=0.5 ; expanded = 2*0.5 = 1.0
    assert out["combined_standard_uncertainty"] == pytest.approx(0.5, abs=1e-6)
    assert out["expanded_uncertainty"] == pytest.approx(1.0, abs=1e-6)
    assert out["coverage_factor"] == 2.0
    # dominant component (characterisation) listed first with larger share
    assert out["components"][0]["component"] == "characterisation"


def test_uncertainty_supports_type_b_rectangular_and_guard_band():
    out = combine_uncertainty(
        [
            {
                "component": "reference_certificate",
                "value": 0.6,
                "input_type": "half_width",
                "distribution": "rectangular",
            },
            {"component": "characterisation", "value": 0.4},
        ],
        coverage_factor=2.0,
        measured_value=1.0,
        tolerance_limit=2.0,
    )

    assert out["components"][0]["component"] == "characterisation"
    assert out["expanded_uncertainty"] == pytest.approx(1.058, abs=1e-3)
    assert out["decision_rule"]["verdict"] == "guard_band_inconclusive"


def test_uncertainty_supports_observations_and_effective_df():
    out = combine_uncertainty(
        [
            {"component": "repeatability", "observations": [0.2, 0.4, 0.3, 0.5]},
            {
                "component": "reference",
                "value": 0.2,
                "input_type": "standard_uncertainty",
                "degrees_freedom": 20,
            },
        ],
        coverage_factor=None,
    )

    assert out["components"][0]["component"] == "reference"
    assert out["effective_degrees_freedom"] is not None
    assert out["coverage_method"] in ("student_t", "fixed_k_2")
    assert out["coverage_factor"] > 0


def test_uncertainty_rejects_empty():
    with pytest.raises(ValueError):
        combine_uncertainty({"repeatability": None})


# ── API ──────────────────────────────────────────────────────────────────────
async def _register(client, email, company):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_characterize_endpoint(client, require_db):
    reg = await _register(client, f"ch-{uuid.uuid4().hex[:8]}@example.com", "Char Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    r = await client.post(
        "/api/v1/colorimetry/characterize",
        json={"patches": _ideal_linear_camera(), "degree": 3},
        headers=h,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["n_patches"] == 24
    assert body["n_terms"] == 13
    assert body["residual"]["mean_delta_e"] < 0.2
    assert len(body["matrix"]) == 13


async def test_uncertainty_endpoint(client, require_db):
    reg = await _register(client, f"un-{uuid.uuid4().hex[:8]}@example.com", "Unc Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    r = await client.post(
        "/api/v1/colorimetry/uncertainty",
        json={"repeatability": 0.3, "characterisation": 0.4, "coverage_factor": 2.0},
        headers=h,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["expanded_uncertainty"] == pytest.approx(1.0, abs=1e-3)
    assert body["unit"] == "delta_e"


async def test_uncertainty_endpoint_advanced_components(client, require_db):
    reg = await _register(client, f"un2-{uuid.uuid4().hex[:8]}@example.com", "Unc Co2")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    r = await client.post(
        "/api/v1/colorimetry/uncertainty",
        json={
            "components": [
                {"component": "repeatability", "observations": [0.2, 0.4, 0.3, 0.5]},
                {
                    "component": "reference",
                    "value": 0.2,
                    "input_type": "standard_uncertainty",
                    "degrees_freedom": 20,
                },
            ],
            "coverage_factor": None,
            "measured_value": 1.0,
            "tolerance_limit": 2.0,
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["effective_degrees_freedom"] is not None
    assert body["decision_rule"]["rule"] == "guard_band"
