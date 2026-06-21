"""Spectral REFLECTANCE ESTIMATION from a measured colour (CIELAB).

⚠️ HARD HONESTY CONTRACT (project rule 7) ⚠️
A reflectance curve recovered from an RGB/Lab colour is NOT a measurement and
NOT the "true" spectrum. RGB carries 3 numbers; a reflectance spectrum has ~31.
The inverse is under-determined — infinitely many spectra (metamers) produce the
SAME colour. This module returns ONE plausible spectrum, the SMOOTHEST metamer
consistent with the measured colour under a known illuminant/observer. It is:
  - always labelled "STIMATA" (estimated),
  - never a basis for an accredited measurement,
  - kept OUT of the sealed Digital Quality Report.
The smoothest-metamer choice is a deterministic, explainable prior (textile dyes
are usually smooth); it cannot see sharp absorption peaks, fluorescence, nor
detect sample/reference metamerism when the two colours match.

Method: among all reflectances r (0..1, 31 bands at 10 nm, 400–700 nm) that
reproduce the measured tristimulus X,Y,Z, pick the one minimising curvature
‖D r‖² (D = 2nd-difference operator) — an equality-constrained quadratic program
with a small ridge for invertibility, then clip to [0,1]. Colour fidelity after
clipping is reported as a round-trip ΔE (CIEDE2000) and folded into a heuristic
(NON-validated) confidence.

CIE data embedded here (1931 2° colour-matching functions + D65 SPD, 10 nm) are
public CIE reference tables, not proprietary ISO/AATCC content (rule 5). A
self-check (the D65 white point ≈ [95.04, 100, 108.88]) guards transcription.
"""

from __future__ import annotations

import math
from typing import Any

from app.vision.delta_e import compute_delta_e_ciede2000

# 400..700 nm at 10 nm — 31 bands.
WAVELENGTHS: list[int] = list(range(400, 701, 10))
N_BANDS = len(WAVELENGTHS)

ESTIMATE_METHOD = "smoothest_metamer_constrained_v1"
ESTIMATE_LABEL = "STIMATA"
DISCLAIMER = (
    "Curva di riflettanza STIMATA dal colore (metamero più liscio), NON una "
    "misura spettrofotometrica. RGB→spettro è sotto-determinato (metamerismo): "
    "questo è uno dei tanti spettri compatibili col colore, scelto come il più "
    "liscio. Non è base di misura accreditata e non entra nel report sigillato."
)

# CIE 1931 2° standard observer colour-matching functions (x̄, ȳ, z̄), 10 nm.
_CMF: dict[int, tuple[float, float, float]] = {
    400: (0.014310, 0.000396, 0.067850),
    410: (0.043510, 0.001210, 0.207400),
    420: (0.134380, 0.004000, 0.645600),
    430: (0.283900, 0.011600, 1.385600),
    440: (0.348280, 0.023000, 1.747060),
    450: (0.336200, 0.038000, 1.772110),
    460: (0.290800, 0.060000, 1.669200),
    470: (0.195360, 0.090980, 1.287640),
    480: (0.095640, 0.139020, 0.812950),
    490: (0.032010, 0.208020, 0.465180),
    500: (0.004900, 0.323000, 0.272000),
    510: (0.009300, 0.503000, 0.158200),
    520: (0.063270, 0.710000, 0.078250),
    530: (0.165500, 0.862000, 0.042160),
    540: (0.290400, 0.954000, 0.020300),
    550: (0.433450, 0.994950, 0.008750),
    560: (0.594500, 0.995000, 0.003900),
    570: (0.762100, 0.952000, 0.002100),
    580: (0.916300, 0.870000, 0.001650),
    590: (1.026300, 0.757000, 0.001100),
    600: (1.062200, 0.631000, 0.000800),
    610: (1.002600, 0.503000, 0.000340),
    620: (0.854450, 0.381000, 0.000190),
    630: (0.642400, 0.265000, 0.000050),
    640: (0.447900, 0.175000, 0.000020),
    650: (0.283500, 0.107000, 0.000000),
    660: (0.164900, 0.061000, 0.000000),
    670: (0.087400, 0.032000, 0.000000),
    680: (0.046770, 0.017000, 0.000000),
    690: (0.022700, 0.008210, 0.000000),
    700: (0.011359, 0.004102, 0.000000),
}

# CIE standard illuminant D65 relative spectral power distribution, 10 nm.
_D65: dict[int, float] = {
    400: 82.7549, 410: 91.4860, 420: 93.4318, 430: 86.6823, 440: 104.8650,
    450: 117.0080, 460: 117.8120, 470: 114.8610, 480: 115.9230, 490: 108.8110,
    500: 109.3540, 510: 107.8020, 520: 104.7900, 530: 107.6890, 540: 104.4050,
    550: 104.0460, 560: 100.0000, 570: 96.3342, 580: 95.7880, 590: 88.6856,
    600: 90.0062, 610: 89.5991, 620: 87.6987, 630: 83.2886, 640: 83.6992,
    650: 80.0268, 660: 80.2146, 670: 82.2778, 680: 78.2842, 690: 69.7213,
    700: 71.6091,
}


def _illuminant_A_spd(wavelengths: list[int]) -> list[float]:
    """CIE standard illuminant A (incandescent, ~2856 K Planckian), computed from
    the CIE definition so there is nothing to mis-transcribe."""
    c2 = 1.435e7  # nm·K (CIE constant for illuminant A)

    def s(wl: float) -> float:
        num = math.exp(c2 / (2848.0 * 560.0)) - 1.0
        den = math.exp(c2 / (2848.0 * wl)) - 1.0
        return 100.0 * (560.0 / wl) ** 5 * (num / den)

    return [s(w) for w in wavelengths]


def illuminant_spd(name: str) -> list[float]:
    """Relative SPD over WAVELENGTHS for a supported illuminant."""
    key = name.upper()
    if key == "D65":
        return [_D65[w] for w in WAVELENGTHS]
    if key == "A":
        return _illuminant_A_spd(WAVELENGTHS)
    raise ValueError(f"Illuminante non supportato: {name!r} (usa D65 o A)")


SUPPORTED_ILLUMINANTS = ("D65", "A")


def _build_observer_matrix(illuminant: str) -> Any:
    """3×N matrix A so that [X,Y,Z] = A @ reflectance, normalised to Y=100 for a
    perfect (r≡1) diffuser. Rows are k·S·x̄, k·S·ȳ, k·S·z̄."""
    import numpy as np

    spd = np.asarray(illuminant_spd(illuminant), dtype=np.float64)
    xbar = np.asarray([_CMF[w][0] for w in WAVELENGTHS], dtype=np.float64)
    ybar = np.asarray([_CMF[w][1] for w in WAVELENGTHS], dtype=np.float64)
    zbar = np.asarray([_CMF[w][2] for w in WAVELENGTHS], dtype=np.float64)
    k = 100.0 / float((spd * ybar).sum())
    return np.vstack([k * spd * xbar, k * spd * ybar, k * spd * zbar])


def white_point(illuminant: str = "D65") -> list[float]:
    """Tristimulus of the perfect diffuser (r≡1) under the illuminant."""
    import numpy as np

    a = _build_observer_matrix(illuminant)
    xyz = a @ np.ones(N_BANDS)
    return [float(v) for v in xyz]


_DELTA = 6.0 / 29.0


def _f_inv(t: float) -> float:
    """Inverse of the CIELAB companding f (used in Lab -> XYZ)."""
    return t**3 if t > _DELTA else 3.0 * _DELTA**2 * (t - 4.0 / 29.0)


def _f_fwd(t: float) -> float:
    """CIELAB companding f (used in XYZ -> Lab)."""
    return t ** (1.0 / 3.0) if t > _DELTA**3 else t / (3.0 * _DELTA**2) + 4.0 / 29.0


def lab_to_xyz(lab: list[float], white: list[float]) -> Any:
    import numpy as np

    L, a, b = lab
    fy = (L + 16.0) / 116.0
    fx = fy + a / 500.0
    fz = fy - b / 200.0
    xn, yn, zn = white
    return np.asarray([xn * _f_inv(fx), yn * _f_inv(fy), zn * _f_inv(fz)])


def xyz_to_lab(xyz: Any, white: list[float]) -> list[float]:
    xn, yn, zn = white
    fx = _f_fwd(float(xyz[0]) / xn)
    fy = _f_fwd(float(xyz[1]) / yn)
    fz = _f_fwd(float(xyz[2]) / zn)
    return [116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)]


def _second_difference_operator() -> Any:
    """(N-2)×N second-difference matrix used as the smoothness penalty."""
    import numpy as np

    d = np.zeros((N_BANDS - 2, N_BANDS))
    for i in range(N_BANDS - 2):
        d[i, i] = 1.0
        d[i, i + 1] = -2.0
        d[i, i + 2] = 1.0
    return d


def estimate_reflectance(
    lab: list[float],
    *,
    illuminant: str = "D65",
    observer: str = "2",
    ridge: float = 1e-3,
) -> dict[str, Any]:
    """Smoothest-metamer reflectance estimate for a measured CIELAB colour.

    Returns a STIMATA result: wavelengths, reflectance (0..1), method, label,
    confidence (heuristic), round-trip ΔE, illuminant/observer, disclaimer.
    """
    import numpy as np

    if observer not in ("2",):
        raise ValueError("Solo osservatore CIE 1931 2° supportato.")

    a = _build_observer_matrix(illuminant)  # 3×N
    white = [float(v) for v in (a @ np.ones(N_BANDS))]
    target_xyz = lab_to_xyz(lab, white)

    # min rᵀMr  s.t.  A r = xyz   ->   r = M⁻¹Aᵀ (A M⁻¹Aᵀ)⁻¹ xyz
    # (errstate: silence benign BLAS FP flags on the small dense solves)
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        d = _second_difference_operator()
        m = d.T @ d + ridge * np.eye(N_BANDS)
        minv_at = np.linalg.solve(m, a.T)  # N×3
        s = a @ minv_at  # 3×3
        r = minv_at @ np.linalg.solve(s, target_xyz)  # N
    r_unclipped = r.copy()
    r = np.clip(r, 0.0, 1.0)

    # colour fidelity after clipping (the honest error of the estimate)
    rt_xyz = a @ r
    rt_lab = xyz_to_lab(rt_xyz, white)
    roundtrip_delta_e = compute_delta_e_ciede2000(lab, rt_lab)

    # heuristic, NON-validated confidence: penalise colour error + clipping
    clip_frac = float(np.mean((r_unclipped < -1e-6) | (r_unclipped > 1.0 + 1e-6)))
    confidence = max(0.0, min(1.0, 1.0 - roundtrip_delta_e / 5.0 - 0.5 * clip_frac))

    warnings: list[str] = []
    if roundtrip_delta_e > 1.0:
        warnings.append(
            f"fedeltà colore ridotta: ΔE round-trip {roundtrip_delta_e:.2f} "
            "(clipping del riflettanza fuori 0..1)"
        )

    return {
        "estimate": True,
        "not_a_measurement": True,
        "label": ESTIMATE_LABEL,
        "method": ESTIMATE_METHOD,
        "engine": "smoothest_metamer",
        "illuminant": illuminant.upper(),
        "observer": observer,
        "wavelengths_nm": list(WAVELENGTHS),
        "reflectance": [round(float(v), 5) for v in r],
        "input_lab": [round(float(v), 3) for v in lab],
        "roundtrip_lab": [round(float(v), 3) for v in rt_lab],
        "roundtrip_delta_e": round(float(roundtrip_delta_e), 3),
        "confidence": round(float(confidence), 3),
        "warnings": warnings,
        "disclaimer": DISCLAIMER,
    }


def render_under_illuminant(
    reflectance: list[float], illuminant: str, *, observer: str = "2"
) -> dict[str, Any]:
    """Predict the CIELAB + sRGB appearance of a (estimated) reflectance under a
    different illuminant — useful to flag metamerism ("does it still match under
    store lighting?"). Accuracy is bounded by the estimate; result is STIMATA."""
    import numpy as np

    if observer != "2":
        raise ValueError("Solo osservatore CIE 1931 2° supportato.")
    r = np.clip(np.asarray(reflectance, dtype=np.float64), 0.0, 1.0)
    if r.shape[0] != N_BANDS:
        raise ValueError(f"reflectance deve avere {N_BANDS} bande (400–700 nm/10).")
    a = _build_observer_matrix(illuminant)
    white = [float(v) for v in (a @ np.ones(N_BANDS))]
    xyz = a @ r
    lab = xyz_to_lab(xyz, white)
    return {
        "estimate": True,
        "not_a_measurement": True,
        "label": ESTIMATE_LABEL,
        "illuminant": illuminant.upper(),
        "observer": observer,
        "lab": [round(float(v), 3) for v in lab],
        "srgb": _xyz_to_srgb(xyz, white),
        "disclaimer": DISCLAIMER,
    }


# Test illuminants available for the metamerism comparison. D65 is the reference
# (daylight); A is warm incandescent/halogen (retail spots). F11/TL84 (shop
# fluorescent) is intentionally NOT here yet — we won't embed an unvalidated
# triband SPD (rule 5/6); it follows once a validated table is added.
METAMERISM_TEST_ILLUMINANTS = ("A",)


def metamerism_pair(
    lab_reference: list[float],
    lab_sample: list[float],
    *,
    reference_illuminant: str = "D65",
    test_illuminants: tuple[str, ...] = METAMERISM_TEST_ILLUMINANTS,
    observer: str = "2",
) -> dict[str, Any]:
    """Estimate the illuminant-dependent colour difference between two samples
    (reference vs sample) from their CIELAB under the reference illuminant.

    ⚠️ HARD LIMITATION (rule 7): both spectra are STIMATE from Lab. If the two
    samples match under the reference illuminant their estimated spectra are
    ~identical by construction, so this method reports MI≈0 — it CANNOT reveal
    real metamerism between samples that match under the reference light. That
    needs MEASURED spectra. It is meaningful for samples that already differ
    under the reference light (how their difference grows/shrinks under another
    light), and as an indicative/visual tool only.

    For each test illuminant we report ΔE (CIEDE2000) and a special metamerism
    index = ΔE under the test light AFTER additively removing the residual
    reference-light mismatch (so a pair matched under the reference reduces to
    the pure test-light divergence, ISO 105-J03 spirit)."""
    est_ref = estimate_reflectance(
        lab_reference, illuminant=reference_illuminant, observer=observer
    )
    est_smp = estimate_reflectance(lab_sample, illuminant=reference_illuminant, observer=observer)
    r_ref = est_ref["reflectance"]
    r_smp = est_smp["reflectance"]

    ref_under_ref = render_under_illuminant(r_ref, reference_illuminant, observer=observer)["lab"]
    smp_under_ref = render_under_illuminant(r_smp, reference_illuminant, observer=observer)["lab"]
    delta_e_reference = round(compute_delta_e_ciede2000(ref_under_ref, smp_under_ref), 3)
    # additive correction that forces a perfect match under the reference light
    correction = [smp_under_ref[i] - ref_under_ref[i] for i in range(3)]

    per_illuminant: list[dict[str, Any]] = []
    for ill in test_illuminants:
        if ill == reference_illuminant:
            continue
        ref_lab = render_under_illuminant(r_ref, ill, observer=observer)["lab"]
        smp_lab = render_under_illuminant(r_smp, ill, observer=observer)["lab"]
        delta_e = round(compute_delta_e_ciede2000(ref_lab, smp_lab), 3)
        corrected_smp = [smp_lab[i] - correction[i] for i in range(3)]
        mi = round(compute_delta_e_ciede2000(ref_lab, corrected_smp), 3)
        per_illuminant.append(
            {
                "illuminant": ill.upper(),
                "delta_e": delta_e,
                "metamerism_index": mi,
                "lab_reference": ref_lab,
                "lab_sample": smp_lab,
            }
        )

    warnings: list[str] = []
    if delta_e_reference < 0.5:
        warnings.append(
            "i campioni combaciano sotto l'illuminante di riferimento: da Lab le "
            "curve STIMATE risultano ~identiche → questo metodo NON può rivelare "
            "metamerismo reale (servono spettri MISURATI)."
        )

    return {
        "estimate": True,
        "not_a_measurement": True,
        "label": ESTIMATE_LABEL,
        "method": "metamerism_index_estimated_v1",
        "reference_illuminant": reference_illuminant.upper(),
        "observer": observer,
        "delta_e_reference": delta_e_reference,
        "per_illuminant": per_illuminant,
        "warnings": warnings,
        "disclaimer": DISCLAIMER,
    }


def _xyz_to_srgb(xyz: Any, white: list[float]) -> list[int]:
    """XYZ (Y up to 100) -> 8-bit sRGB for a preview swatch (display only)."""
    import numpy as np

    xn = np.asarray(xyz, dtype=np.float64) / 100.0
    m = np.array(
        [
            [3.2406, -1.5372, -0.4986],
            [-0.9689, 1.8758, 0.0415],
            [0.0557, -0.2040, 1.0570],
        ]
    )
    rgb = m @ xn
    rgb = np.clip(rgb, 0.0, 1.0)
    srgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - 0.055)
    return [int(round(float(c) * 255)) for c in np.clip(srgb, 0.0, 1.0)]
