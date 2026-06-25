"""Camera characterisation: fit a camera RGB → CIE XYZ/Lab transform from a
ColorChecker shot, so the captured colour is colorimeter-grade (not raw sRGB).

This is the HONEST path toward a spectrophotometer-equivalent ΔE/grade for an
accredited scope: we do NOT reconstruct spectra — we make the camera's measured
colour agree with reference colorimetry. The transform is fitted per kit/lighting
from the 24 ColorChecker patches by ROOT-POLYNOMIAL regression (Finlayson,
Mackiewicz & Hurlbert 2015), which is exposure-invariant. Fit quality is reported
as a residual ΔE budget (CIEDE2000) that feeds the measurement-uncertainty
estimate (ISO 17025).

Scope honesty: a characterised camera matches a colorimeter for opaque samples
under the capture illuminant, within the validated ΔE. It does NOT replace a
spectrophotometer for multi-illuminant metamerism, optical brighteners/UV, or
gloss/effect colours.
"""

from __future__ import annotations

from typing import Any

from app.vision.delta_e import compute_delta_e_ciede2000
from app.vision.spectral import lab_to_xyz, xyz_to_lab

# X-Rite ColorChecker Classic — 24-patch reference CIELAB (D65, 2°), public
# community-averaged values (BabelColor). Order: row-major, patch 1..24.
COLORCHECKER_LAB: list[tuple[float, float, float]] = [
    (37.54, 14.37, 14.92),    # 1 dark skin
    (64.66, 19.27, 17.50),    # 2 light skin
    (49.32, -3.82, -22.54),   # 3 blue sky
    (43.46, -12.74, 22.72),   # 4 foliage
    (54.94, 9.61, -24.79),    # 5 blue flower
    (70.48, -32.26, -0.37),   # 6 bluish green
    (62.73, 35.83, 56.50),    # 7 orange
    (39.43, 10.75, -45.17),   # 8 purplish blue
    (50.57, 48.64, 16.67),    # 9 moderate red
    (30.10, 22.54, -20.87),   # 10 purple
    (71.77, -24.13, 58.19),   # 11 yellow green
    (71.51, 18.24, 67.37),    # 12 orange yellow
    (28.37, 15.42, -49.80),   # 13 blue
    (54.38, -39.72, 32.27),   # 14 green
    (42.43, 51.05, 28.62),    # 15 red
    (81.80, 2.67, 80.41),     # 16 yellow
    (50.63, 51.28, -14.12),   # 17 magenta
    (49.57, -29.71, -28.32),  # 18 cyan
    (95.19, -1.03, 2.93),     # 19 white
    (81.29, -0.57, 0.44),     # 20 neutral 8
    (66.89, -0.75, -0.06),    # 21 neutral 6.5
    (50.76, -0.13, 0.14),     # 22 neutral 5
    (35.63, -0.46, -0.48),    # 23 neutral 3.5
    (20.64, 0.07, -0.46),     # 24 black
]

_D65_WHITE = [95.047, 100.0, 108.883]


def colorchecker_xyz() -> list[list[float]]:
    """Reference XYZ (Y on 0..100, D65) of the 24 ColorChecker patches."""
    return [list(lab_to_xyz(list(lab), _D65_WHITE)) for lab in COLORCHECKER_LAB]


def _n_terms(degree: int) -> int:
    return {1: 3, 2: 6, 3: 13}[degree]


def root_poly_features(rgb01: Any, degree: int) -> Any:
    """Root-polynomial feature expansion of a normalised (0..1) RGB triple.

    INPUT MUST BE LINEAR camera RGB (RAW / ProRAW-linearised) — NOT gamma-encoded
    sRGB. Root-polynomial models a smooth linear-domain relationship; feeding a
    tone curve wrecks the fit. degree 1 → [R,G,B]; degree 2 adds the 3 degree-2
    root terms; degree 3 adds the 7 degree-3 root terms (Finlayson root-
    polynomial, exposure-invariant)."""
    import numpy as np

    r, g, b = (float(rgb01[0]), float(rgb01[1]), float(rgb01[2]))
    feats = [r, g, b]
    if degree >= 2:
        feats += [
            np.sqrt(r * g),
            np.sqrt(g * b),
            np.sqrt(r * b),
        ]
    if degree >= 3:
        feats += [
            np.cbrt(r * r * g),
            np.cbrt(r * r * b),
            np.cbrt(g * g * r),
            np.cbrt(g * g * b),
            np.cbrt(b * b * r),
            np.cbrt(b * b * g),
            np.cbrt(r * g * b),
        ]
    return np.asarray(feats, dtype=np.float64)


def _to01(rgb: Any) -> Any:
    import numpy as np

    a = np.asarray(rgb, dtype=np.float64)
    return a / 255.0 if float(a.max()) > 1.0 else a


def fit_camera_transform(
    rgb_patches: list[list[float]],
    *,
    degree: int = 2,
    reference_lab: list[list[float]] | None = None,
) -> dict[str, Any]:
    """Least-squares fit of a root-polynomial camera RGB → XYZ transform from the
    measured patch RGBs and the reference patch colours.

    Returns the matrix (n_terms×3), degree and a residual ΔE budget (the
    characterisation accuracy) used downstream for uncertainty."""
    import numpy as np

    if degree not in (1, 2, 3):
        raise ValueError("degree deve essere 1, 2 o 3")
    ref_lab = reference_lab if reference_lab is not None else [list(c) for c in COLORCHECKER_LAB]
    n = len(rgb_patches)
    if n != len(ref_lab):
        raise ValueError("numero patch RGB ≠ numero patch di riferimento")
    if n < _n_terms(degree):
        raise ValueError(
            f"servono almeno {_n_terms(degree)} patch per grado {degree} (ricevute {n})"
        )

    ref_xyz = np.asarray([lab_to_xyz(list(lab), _D65_WHITE) for lab in ref_lab], dtype=np.float64)
    phi = np.vstack([root_poly_features(_to01(p), degree) for p in rgb_patches])  # n×t
    # solve phi @ M = ref_xyz  (least squares), M: t×3
    matrix, *_ = np.linalg.lstsq(phi, ref_xyz, rcond=None)

    pred_xyz = phi @ matrix
    per_patch = []
    deltas = []
    for i in range(n):
        pred_lab = xyz_to_lab(pred_xyz[i], _D65_WHITE)
        de = compute_delta_e_ciede2000(ref_lab[i], pred_lab)
        deltas.append(de)
        per_patch.append({"patch": i + 1, "delta_e": round(float(de), 3)})

    deltas_arr = np.asarray(deltas)
    residual = {
        "mean_delta_e": round(float(deltas_arr.mean()), 3),
        "max_delta_e": round(float(deltas_arr.max()), 3),
        "rms_delta_e": round(float(np.sqrt((deltas_arr**2).mean())), 3),
        "p95_delta_e": round(float(np.percentile(deltas_arr, 95)), 3),
    }
    return {
        "method": "root_polynomial",
        "degree": degree,
        "n_terms": _n_terms(degree),
        "n_patches": n,
        "reference": "ColorChecker24_D65",
        "matrix": [[round(float(v), 8) for v in row] for row in matrix],
        "residual": residual,
        "per_patch": per_patch,
    }


def apply_camera_transform(
    matrix: list[list[float]], rgb: list[float], *, degree: int = 2
) -> dict[str, Any]:
    """Map a single camera RGB through a fitted transform to XYZ + CIELAB."""
    import numpy as np

    m = np.asarray(matrix, dtype=np.float64)
    feats = root_poly_features(_to01(rgb), degree)
    xyz = feats @ m
    lab = xyz_to_lab(xyz, _D65_WHITE)
    return {
        "xyz": [round(float(v), 4) for v in xyz],
        "lab": [round(float(v), 3) for v in lab],
    }
