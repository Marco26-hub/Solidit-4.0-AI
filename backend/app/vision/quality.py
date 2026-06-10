"""Capture quality gate for the multifibre photo.

iPhone/phone sensors are a capture QUALITY GATE, not lab metrology by themselves
(architecture rule 9). We score blur, exposure and strip fill, emit warnings and
an overall acceptability flag. These feed the result's provenance so a reviewer
can judge whether a capture is fit for a pre-validation report.
"""

from __future__ import annotations

from typing import Any

# Conservative defaults — tune against the validation pilot (Phase 8).
BLUR_MIN = 60.0  # variance-of-Laplacian; below this the strip is likely blurred
EXPOSURE_LOW = 40.0  # mean luminance (0..255) below -> underexposed
EXPOSURE_HIGH = 220.0  # above -> overexposed
CLIP_MAX_PCT = 0.10  # >10% clipped highlights/shadows -> warning
FILL_MIN = 0.10  # strip should occupy at least this fraction of the frame


def assess_capture(image_rgb: Any, fill_ratio: float | None = None) -> dict[str, Any]:
    """Return blur/exposure/fill metrics + warnings + acceptable flag."""
    import numpy as np
    from skimage import color, filters

    arr = np.asarray(image_rgb)[:, :, :3].astype(np.float64)
    gray = color.rgb2gray(arr / 255.0)

    # blur: variance of the Laplacian (higher = sharper)
    lap = filters.laplace(gray)
    blur_score = float(np.var(lap) * 1e4)

    lum = gray * 255.0
    exposure_mean = float(lum.mean())
    clipped = float(((lum < 5) | (lum > 250)).mean())

    warnings: list[str] = []
    if blur_score < BLUR_MIN:
        warnings.append("blur: immagine poco nitida (rischio sfocatura)")
    if exposure_mean < EXPOSURE_LOW:
        warnings.append("exposure: sottoesposta")
    elif exposure_mean > EXPOSURE_HIGH:
        warnings.append("exposure: sovraesposta")
    if clipped > CLIP_MAX_PCT:
        warnings.append("exposure: zone bruciate/nere oltre soglia")
    if fill_ratio is not None and fill_ratio < FILL_MIN:
        warnings.append("framing: la striscia occupa poco del fotogramma")

    return {
        "blur_score": round(blur_score, 2),
        "exposure_mean": round(exposure_mean, 1),
        "clipped_pct": round(clipped, 4),
        "fill_ratio": round(fill_ratio, 4) if fill_ratio is not None else None,
        "warnings": warnings,
        "acceptable": len(warnings) == 0,
    }
