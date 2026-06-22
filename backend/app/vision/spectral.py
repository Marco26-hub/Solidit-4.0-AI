"""Spectral REFLECTANCE ESTIMATION from a measured colour (CIELAB).

⚠️ HARD HONESTY CONTRACT (project rule 7) ⚠️
A reflectance curve recovered from an RGB/Lab colour is NOT a measurement and
NOT the "true" spectrum. RGB carries 3 numbers; a reflectance spectrum has ~31.
The inverse is under-determined — infinitely many spectra (metamers) produce the
SAME colour. This module returns ONE plausible spectrum (a smooth metamer)
consistent with the measured colour under a known illuminant/observer. It is:
  - always labelled "STIMATA" (estimated),
  - never a basis for an accredited measurement,
  - kept OUT of the sealed Digital Quality Report.
The smooth-metamer choice is a deterministic, explainable prior (textile dyes are
usually smooth); it cannot see sharp absorption peaks, fluorescence, nor detect
sample/reference metamerism when the two colours match.

Method — LHTSS (Least Hyperbolic Tangent Slope Squared, Scott Burns): the
reflectance is reparametrised ρ = (tanh z + 1)/2 so ρ ∈ (0,1) for ALL z (the
bounds are built in — no clipping). We minimise the squared slope of z subject to
the exact colour constraint T·ρ = XYZ, solving the Lagrangian KKT system by
damped Newton. When the colour lies inside the object-colour solid this
reproduces it EXACTLY (round-trip ΔE ≈ 0, even for saturated colours that the old
unconstrained-then-clip method distorted); when it is out of gamut Newton stalls
and the result is flagged (in_gamut=False, lower confidence). Confidence is the
colour round-trip fidelity (ΔE CIEDE2000) — a heuristic, NON-validated number;
it does NOT claim spectral accuracy (no true spectrum exists to validate against).

Entry points: estimate_reflectance(lab) · reflectance_from_xyz(xyz) ·
reflectance_from_rgb(rgb) — the last goes sRGB→linear→XYZ (D65) directly, the
right model for an iPhone pixel.

CIE data embedded here (1931 2° colour-matching functions + D65 SPD, 10 nm) are
public CIE reference tables, not proprietary ISO/AATCC content (rule 5). The
observer matrix is rescaled so a perfect diffuser hits the canonical white point
exactly (consistent with the sRGB→XYZ matrix), which also self-checks the tables.
"""

from __future__ import annotations

import math
from typing import Any

from app.vision.delta_e import compute_delta_e_ciede2000

# 400..700 nm at 10 nm — 31 bands.
WAVELENGTHS: list[int] = list(range(400, 701, 10))
N_BANDS = len(WAVELENGTHS)

ESTIMATE_METHOD = "lhtss_burns_v2"
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

# Canonical CIE 2° white points. We rescale each observer-matrix row so a perfect
# diffuser (r≡1) reproduces these exactly: it cancels the small finite-bandwidth
# (10 nm) integration error so RGB white maps to the standard white and the
# sRGB→XYZ matrix stays consistent with our T.
_CANONICAL_WHITE: dict[str, tuple[float, float, float]] = {
    "D65": (95.047, 100.0, 108.883),
    "A": (109.850, 100.0, 35.585),
}


def _build_observer_matrix(illuminant: str) -> Any:
    """3×N matrix T so that [X,Y,Z] = T @ reflectance, with the perfect (r≡1)
    diffuser landing exactly on the canonical white point. Rows ∝ S·x̄, S·ȳ, S·z̄."""
    import numpy as np

    key = illuminant.upper()
    spd = np.asarray(illuminant_spd(key), dtype=np.float64)
    xbar = np.asarray([_CMF[w][0] for w in WAVELENGTHS], dtype=np.float64)
    ybar = np.asarray([_CMF[w][1] for w in WAVELENGTHS], dtype=np.float64)
    zbar = np.asarray([_CMF[w][2] for w in WAVELENGTHS], dtype=np.float64)
    rows = np.vstack([spd * xbar, spd * ybar, spd * zbar])
    white = _CANONICAL_WHITE.get(key, (None, 100.0, None))
    ones = np.ones(N_BANDS)
    for i in range(3):
        target = white[i]
        if target is None:  # unknown illuminant: just normalise Y to 100
            target = 100.0 if i == 1 else float(rows[i] @ ones)
        rows[i] *= target / float(rows[i] @ ones)
    return rows


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


def _smoothness_gram() -> Any:
    """KᵀK with K the first-difference operator — the slope² penalty on z
    (Burns LHTSS). Tiny ridge lifts the constant-vector nullspace."""
    import numpy as np

    k = np.zeros((N_BANDS - 1, N_BANDS))
    for i in range(N_BANDS - 1):
        k[i, i] = -1.0
        k[i, i + 1] = 1.0
    return k.T @ k + 1e-8 * np.eye(N_BANDS)


def _solve_lhtss(target_xyz: Any, t_obs: Any, *, max_iter: int = 60) -> tuple[Any, bool, int]:
    """Least Hyperbolic Tangent Slope Squared (Scott Burns).

    Find reflectance ρ∈(0,1) reproducing the tristimulus `target_xyz` under the
    observer matrix `t_obs` (3×N) while minimising the squared slope of the
    pre-image z, where ρ = (tanh z + 1)/2. Solves the Lagrangian KKT system
        F₁ = D z + diag(ρ′)·Tᵀλ = 0
        F₂ = T·ρ − b = 0
    by damped Newton. Returns (ρ, converged, iterations). When the colour is
    outside the object-colour solid the equality is infeasible: Newton stalls and
    we return the closest ρ with converged=False (caller flags it)."""
    import numpy as np

    d = _smoothness_gram()
    b = np.asarray(target_xyz, dtype=np.float64)
    z = np.zeros(N_BANDS)
    lam = np.zeros(3)

    def residual(zv: Any, lv: Any) -> Any:
        t = np.tanh(zv)
        rho = (t + 1.0) / 2.0
        rho1 = (1.0 - t * t) / 2.0
        f1 = d @ zv + rho1 * (t_obs.T @ lv)
        f2 = t_obs @ rho - b
        return np.concatenate([f1, f2])

    converged = False
    iters = 0
    with np.errstate(over="ignore", invalid="ignore"):
        for it in range(1, max_iter + 1):
            iters = it
            t = np.tanh(z)
            rho1 = (1.0 - t * t) / 2.0
            rho2 = -(1.0 - t * t) * t  # d²ρ/dz²
            ttl = t_obs.T @ lam
            j11 = d + np.diag(rho2 * ttl)
            j12 = rho1[:, None] * t_obs.T  # N×3
            j21 = t_obs * rho1[None, :]  # 3×N
            jac = np.block([[j11, j12], [j21, np.zeros((3, 3))]])
            f = residual(z, lam)
            nrm = float(np.linalg.norm(f))
            if nrm < 1e-9:
                converged = True
                break
            try:
                step = np.linalg.solve(jac, -f)
            except np.linalg.LinAlgError:
                break
            # backtracking line search on ‖F‖
            alpha = 1.0
            for _ in range(25):
                zn = z + alpha * step[:N_BANDS]
                ln = lam + alpha * step[N_BANDS:]
                if float(np.linalg.norm(residual(zn, ln))) < nrm:
                    break
                alpha *= 0.5
            z = z + alpha * step[:N_BANDS]
            lam = lam + alpha * step[N_BANDS:]
        else:
            converged = float(np.linalg.norm(residual(z, lam))) < 1e-9

    rho = (np.tanh(z) + 1.0) / 2.0
    return rho, converged, iters


def _build_estimate(
    target_xyz: Any,
    t_obs: Any,
    *,
    illuminant: str,
    observer: str,
    input_lab: list[float] | None = None,
) -> dict[str, Any]:
    """Run LHTSS and package the STIMATA result dict (shared by the Lab/XYZ/RGB
    entry points)."""
    import numpy as np

    white = [float(v) for v in (t_obs @ np.ones(N_BANDS))]
    if input_lab is None:
        input_lab = xyz_to_lab(np.asarray(target_xyz, dtype=np.float64), white)

    rho, converged, iters = _solve_lhtss(target_xyz, t_obs)
    rt_xyz = t_obs @ rho
    rt_lab = xyz_to_lab(rt_xyz, white)
    roundtrip_delta_e = compute_delta_e_ciede2000(input_lab, rt_lab)
    in_gamut = bool(converged and roundtrip_delta_e < 1.0)

    confidence = max(
        0.0, min(1.0, 1.0 - roundtrip_delta_e / 5.0 - (0.0 if converged else 0.3))
    )
    warnings: list[str] = []
    if not in_gamut:
        warnings.append(
            f"colore al limite/fuori dal gamut riflettanza: ricostruzione "
            f"approssimata (ΔE round-trip {roundtrip_delta_e:.2f}). Su colori molto "
            "saturi nessuna riflettanza 0..1 riproduce esattamente il colore."
        )

    return {
        "estimate": True,
        "not_a_measurement": True,
        "label": ESTIMATE_LABEL,
        "method": ESTIMATE_METHOD,
        "engine": "lhtss",
        "illuminant": illuminant.upper(),
        "observer": observer,
        "in_gamut": in_gamut,
        "iterations": int(iters),
        "wavelengths_nm": list(WAVELENGTHS),
        "reflectance": [round(float(v), 5) for v in rho],
        "input_lab": [round(float(v), 3) for v in input_lab],
        "roundtrip_lab": [round(float(v), 3) for v in rt_lab],
        "roundtrip_delta_e": round(float(roundtrip_delta_e), 3),
        "confidence": round(float(confidence), 3),
        "warnings": warnings,
        "disclaimer": DISCLAIMER,
    }


def estimate_reflectance(
    lab: list[float],
    *,
    illuminant: str = "D65",
    observer: str = "2",
) -> dict[str, Any]:
    """LHTSS reflectance estimate for a measured CIELAB colour.

    Returns a STIMATA result: wavelengths, reflectance (0..1), method, label,
    confidence (heuristic), round-trip ΔE, illuminant/observer, disclaimer."""
    if observer not in ("2",):
        raise ValueError("Solo osservatore CIE 1931 2° supportato.")
    t_obs = _build_observer_matrix(illuminant)
    white = [float(v) for v in (t_obs @ _np_ones())]
    target_xyz = lab_to_xyz(lab, white)
    return _build_estimate(
        target_xyz, t_obs, illuminant=illuminant, observer=observer, input_lab=lab
    )


def _np_ones() -> Any:
    import numpy as np

    return np.ones(N_BANDS)


def _srgb_to_xyz(rgb: Any) -> Any:
    """sRGB (8-bit or 0..1) → CIE XYZ (D65, Y on 0..100). The standard sRGB→XYZ
    matrix; its white maps to the canonical D65 white our observer matrix uses."""
    import numpy as np

    c = np.asarray(rgb, dtype=np.float64)
    if float(c.max()) > 1.0:
        c = c / 255.0
    c = np.clip(c, 0.0, 1.0)
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ]
    )
    return (m @ lin) * 100.0


def reflectance_from_xyz(
    xyz: list[float], *, illuminant: str = "D65", observer: str = "2"
) -> dict[str, Any]:
    """LHTSS reflectance estimate from a tristimulus XYZ (Y on 0..100)."""
    if observer not in ("2",):
        raise ValueError("Solo osservatore CIE 1931 2° supportato.")
    t_obs = _build_observer_matrix(illuminant)
    return _build_estimate(xyz, t_obs, illuminant=illuminant, observer=observer)


def reflectance_from_rgb(
    rgb: list[float], *, observer: str = "2"
) -> dict[str, Any]:
    """LHTSS reflectance estimate from an sRGB triplet (e.g. an iPhone pixel).

    sRGB is a D65-referenced encoding, so the reflectance is reconstructed under
    D65; render it under other illuminants afterwards. STIMATA, never a measure."""
    target_xyz = [float(v) for v in _srgb_to_xyz(rgb)]
    out = reflectance_from_xyz(target_xyz, illuminant="D65", observer=observer)
    rgb8 = rgb if max(rgb) > 1 else [v * 255 for v in rgb]
    out["input_rgb"] = [int(round(float(c))) for c in rgb8]
    return out


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
