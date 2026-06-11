"""In-frame grey-scale / neutral reference detection + colour correction.

ISO 105-A11 logic (and the approach the Kuraray Colour Fastness app uses): the
capture includes a neutral grey reference in the SAME photo, taken under the same
light. We detect the brightest, most neutral, most uniform patch and use it to
white-balance the whole image BEFORE Lab extraction. This is an in-frame colour
correction that does not need a per-device calibration matrix — and it makes ΔE
robust to the light's colour cast.

We do NOT claim spectral measurement; this is an imaging correction anchored to a
physical neutral reference in frame.
"""

from __future__ import annotations

from typing import Any


def find_neutral_reference(
    image_rgb: Any,
    *,
    grid: int = 12,
    min_brightness: float = 150.0,
    max_chroma_ratio: float = 0.06,
) -> dict | None:
    """Scan a grid of patches; return the best neutral (low-chroma), bright,
    uniform patch as {rgb, chroma, uniformity, loc} — the in-frame white/grey
    reference. Returns None if no confident neutral patch is found."""
    import numpy as np

    arr = np.asarray(image_rgb)[:, :, :3].astype(np.float64)
    h, w = arr.shape[:2]
    ph, pw = max(1, h // grid), max(1, w // grid)
    best: dict | None = None
    for gy in range(grid):
        for gx in range(grid):
            patch = arr[gy * ph : (gy + 1) * ph, gx * pw : (gx + 1) * pw]
            if patch.size == 0:
                continue
            flat = patch.reshape(-1, 3)
            mean = flat.mean(axis=0)
            m = float(mean.mean())
            if m < min_brightness:
                continue
            chroma = float(mean.max() - mean.min()) / (m + 1e-6)
            if chroma > max_chroma_ratio:
                continue
            std = float(flat.std(axis=0).mean())
            score = m - 2.0 * std  # bright + uniform wins
            if best is None or score > best["score"]:
                best = {
                    "rgb": [float(x) for x in mean],
                    "chroma": round(chroma, 4),
                    "uniformity": round(max(0.0, 1.0 - std / 30.0), 3),
                    "loc": [gy, gx],
                    "score": score,
                }
    if best is not None:
        best.pop("score", None)
    return best


def neutral_white_balance(image_rgb: Any, white_rgb: list[float]) -> Any:
    """Apply a per-channel gain so the neutral reference becomes achromatic
    (R=G=B). Gains are clamped to [0.5, 2.0] so a wrong reference can't blow up
    the image. Returns a uint8 image."""
    import numpy as np

    arr = np.asarray(image_rgb)
    w = np.asarray(white_rgb, dtype=np.float64)
    target = float(w.mean())
    gains = np.clip(target / np.clip(w, 1.0, None), 0.5, 2.0)
    out = np.clip(arr[:, :, :3].astype(np.float64) * gains, 0, 255)
    return out.astype(np.uint8)
