"""Automatic multifibre strip recognition.

The capture is just the multifibre strip. We (1) locate the strip in the frame
(foreground vs uniform background), (2) find its long axis, (3) segment it into N
bands — N = number of fibres in the selected strip profile — and snap the band
boundaries to the real colour seams, then (4) map band i -> fibre i in the
profile order (the multifibre fibre sequence is fixed by the standard).

Bands are returned IN ORDER along the long axis. Convention: the operator places
the strip with the standard's first fibre at the left (horizontal) or top
(vertical). Orientation ambiguity is not resolvable from pixels alone without a
fiducial marker, so the order follows this placement convention.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def _detect_strip_bbox(arr: Any) -> tuple[int, int, int, int, float]:
    """Return (y0, y1, x0, x1, fill_ratio). Estimates background from the four
    corners; the strip is the bounding box of pixels differing from it. Falls
    back to the full frame when the strip fills it (corners == strip)."""
    import numpy as np

    h, w = arr.shape[:2]
    rgb = arr[:, :, :3].astype(np.float64)
    cs = max(4, min(h, w) // 20)  # corner patch size
    corners = np.concatenate(
        [
            rgb[:cs, :cs].reshape(-1, 3),
            rgb[:cs, -cs:].reshape(-1, 3),
            rgb[-cs:, :cs].reshape(-1, 3),
            rgb[-cs:, -cs:].reshape(-1, 3),
        ]
    )
    bg = np.median(corners, axis=0)
    dist = np.sqrt(((rgb - bg) ** 2).sum(axis=2))
    # adaptive threshold: background patches are tight; strip differs clearly
    thr = max(25.0, float(np.percentile(dist, 60)))
    mask = dist > thr

    # use per-row/col coverage so a few stray foreground pixels don't define the
    # bbox; a real strip is a band where most of the slice is foreground
    row_cov = mask.mean(axis=1)
    col_cov = mask.mean(axis=0)
    fg_rows = np.where(row_cov > 0.30)[0]
    fg_cols = np.where(col_cov > 0.30)[0]
    if fg_rows.size == 0 or fg_cols.size == 0:
        return 0, h, 0, w, 1.0
    y0, y1 = int(fg_rows.min()), int(fg_rows.max()) + 1
    x0, x1 = int(fg_cols.min()), int(fg_cols.max()) + 1
    span_y, span_x = (y1 - y0) / h, (x1 - x0) / w
    # Accept the crop only when it looks like a strip filling most of the frame
    # (we are just trimming small margins on a contrasting background). Otherwise
    # — including the white-strip-on-white-background case where detection
    # collapses onto the stained band — fall back to the full frame.
    if min(span_y, span_x) < 0.55:
        return 0, h, 0, w, 1.0
    bbox_fill = round(span_y * span_x, 4)
    return y0, y1, x0, x1, bbox_fill


def _snap_boundaries(profile_grad: Any, n: int, length: int) -> list[int]:
    """Start from equal-width boundaries and snap each to the strongest colour
    seam within a ±window, keeping them strictly increasing."""
    import numpy as np

    eq = [round(i * length / n) for i in range(n + 1)]
    if profile_grad is None or length < n * 4:
        return eq
    win = max(2, int(length / n * 0.25))
    snapped = [0]
    for i in range(1, n):
        center = eq[i]
        lo = max(snapped[-1] + 2, center - win)
        hi = min(length - 2, center + win)
        if hi <= lo:
            snapped.append(center)
            continue
        local = profile_grad[lo:hi]
        snapped.append(int(lo + int(np.argmax(local))) if local.size else center)
    snapped.append(length)
    # enforce strictly increasing
    for i in range(1, len(snapped)):
        if snapped[i] <= snapped[i - 1]:
            snapped[i] = min(length, snapped[i - 1] + 1)
    return snapped


def detect_and_split(image_rgb: Any, fibers: Sequence[str]) -> dict[str, Any]:
    """Locate the strip, segment N ordered bands and map them to fibre codes.

    Returns: {
        "rois": {fiber: RGB ndarray (central crop)},
        "order": [fiber, ...],
        "orientation": "horizontal"|"vertical",
        "bbox": [y0,y1,x0,x1],
        "fill_ratio": float,
        "boundary_method": "snapped"|"equal",
        "band_confidence": {fiber: 0..1},
    }
    """
    import numpy as np

    arr = np.asarray(image_rgb)
    n = max(1, len(fibers))
    y0, y1, x0, x1, fill = _detect_strip_bbox(arr)
    strip = arr[y0:y1, x0:x1, :3]
    sh, sw = strip.shape[:2]
    horizontal = sw >= sh
    length = sw if horizontal else sh

    # mean colour per slice along the long axis -> seam gradient
    if horizontal:
        line = strip.astype(np.float64).mean(axis=0)  # (W,3)
    else:
        line = strip.astype(np.float64).mean(axis=1)  # (H,3)
    if line.shape[0] >= 2:
        grad = np.sqrt(((np.diff(line, axis=0)) ** 2).sum(axis=1))  # (L-1,)
        grad = np.concatenate([grad, grad[-1:]])
    else:
        grad = None

    bounds = _snap_boundaries(grad, n, length)
    method = "snapped" if grad is not None and length >= n * 4 else "equal"

    rois: dict[str, Any] = {}
    confidence: dict[str, float] = {}
    for i, fiber in enumerate(fibers):
        b0, b1 = bounds[i], bounds[i + 1]
        pad = int((b1 - b0) * 0.2)
        lo, hi = b0 + pad, max(b0 + pad + 1, b1 - pad)
        if horizontal:
            cy0, cy1 = int(sh * 0.2), int(sh * 0.8)
            roi = strip[cy0:cy1, lo:hi, :3]
        else:
            cx0, cx1 = int(sw * 0.2), int(sw * 0.8)
            roi = strip[lo:hi, cx0:cx1, :3]
        if roi.size == 0:
            roi = strip[:, :, :3]
        rois[fiber] = roi
        # confidence: uniform band (low intra-band colour stddev) -> high
        std = float(np.asarray(roi, dtype=np.float64).reshape(-1, 3).std(axis=0).mean())
        confidence[fiber] = round(max(0.0, min(1.0, 1.0 - std / 60.0)), 3)

    return {
        "rois": rois,
        "order": list(fibers),
        "orientation": "horizontal" if horizontal else "vertical",
        "bbox": [int(y0), int(y1), int(x0), int(x1)],
        "fill_ratio": fill,
        "boundary_method": method,
        "band_confidence": confidence,
    }
