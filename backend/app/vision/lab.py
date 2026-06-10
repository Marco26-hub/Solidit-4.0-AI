"""RGB -> CIELAB conversion and multifiber ROI extraction.

ROI split: the canonical strip is divided into N equal bands (N = number of
fibres in the selected strip profile) along its longer axis; the central 60% of
each band is averaged to avoid seams/edges."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def rgb_to_lab(rgb_patch: Any) -> list[float]:
    """Mean CIELAB of an RGB patch (HxWx3, 0..255)."""
    import numpy as np
    from skimage import color

    rgb = np.asarray(rgb_patch, dtype=np.float64)
    if rgb.max() > 1.0:
        rgb = rgb / 255.0
    lab = color.rgb2lab(rgb)
    mean = lab.reshape(-1, 3).mean(axis=0)
    return [float(mean[0]), float(mean[1]), float(mean[2])]


def extract_multifiber_rois(image_rgb: Any, fibers: Sequence[str]) -> dict[str, Any]:
    """Return {fiber_code: RGB ROI ndarray} by splitting the strip into len(fibers)
    bands along the longer axis (central 60% of each band)."""
    import numpy as np

    arr = np.asarray(image_rgb)
    h, w = arr.shape[:2]
    n = max(1, len(fibers))
    out: dict[str, Any] = {}

    if w >= h:  # horizontal strip -> vertical bands
        band = w / n
        cy0, cy1 = int(h * 0.2), int(h * 0.8)
        for i, fiber in enumerate(fibers):
            x0, x1 = int(i * band), int((i + 1) * band)
            pad = int((x1 - x0) * 0.2)
            out[fiber] = arr[cy0:cy1, x0 + pad : x1 - pad, :3]
    else:  # vertical strip -> horizontal bands
        band = h / n
        cx0, cx1 = int(w * 0.2), int(w * 0.8)
        for i, fiber in enumerate(fibers):
            y0, y1 = int(i * band), int((i + 1) * band)
            pad = int((y1 - y0) * 0.2)
            out[fiber] = arr[y0 + pad : y1 - pad, cx0:cx1, :3]
    return out
