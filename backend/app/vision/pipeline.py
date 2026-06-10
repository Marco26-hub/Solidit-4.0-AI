"""End-to-end multifiber staining analysis from a strip photo.

The capture is just the multifibre strip. We assess capture quality, locate the
strip, segment it into N ordered bands (mapped to the profile's fibre order),
then per fibre compute sample Lab, ΔE vs the (unstained) reference and a
grey-scale staining grade. Brand-rule pass/fail is applied by the service layer.

Geometry (homography) + markers (ArUco) need OpenCV and remain a later hardening
step; today the strip is auto-located from the frame and split by colour seams.
"""

from __future__ import annotations

from collections.abc import Sequence
from io import BytesIO
from typing import Any

from app.vision import ALGORITHM_VERSION
from app.vision.color_correction import apply_color_matrix
from app.vision.delta_e import compute_delta_e_ciede2000
from app.vision.grading import DEFAULT_STAINING_THRESHOLDS, map_delta_e_to_grade
from app.vision.lab import rgb_to_lab
from app.vision.quality import assess_capture
from app.vision.segmentation import detect_and_split


def analyze_multifiber(
    image_bytes: bytes,
    fibers: Sequence[str],
    reference_lab: dict[str, dict],
    *,
    color_matrix: Any = None,
    thresholds: list[dict] | None = None,
) -> dict[str, Any]:
    """fibers: ordered fibre codes (from the strip profile).
    reference_lab: {fiber: {"L":..,"a":..,"b":..}} — the unstained reference."""
    import numpy as np
    from PIL import Image

    thresholds = thresholds or DEFAULT_STAINING_THRESHOLDS
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    arr: Any = np.asarray(image)
    if color_matrix is not None:
        arr = apply_color_matrix(arr, color_matrix)

    seg = detect_and_split(arr, fibers)
    rois = seg["rois"]
    quality = assess_capture(arr, fill_ratio=seg.get("fill_ratio"))

    # surface (do NOT hide) that no device colour-correction was applied: ΔE is
    # computed on raw camera RGB, which is a real metrological limitation
    colour_correction = "applied" if color_matrix is not None else "none"
    pipeline_warnings = list(quality["warnings"])
    if colour_correction == "none":
        pipeline_warnings.append(
            "colour_correction: non applicata (RGB camera grezzo, nessuna taratura device)"
        )

    out_fibers: dict[str, Any] = {}
    for fiber in fibers:
        ref = reference_lab.get(fiber)
        if ref is None or fiber not in rois:
            continue
        sample_lab = rgb_to_lab(rois[fiber])
        ref_lab = [float(ref["L"]), float(ref["a"]), float(ref["b"])]
        delta_e = compute_delta_e_ciede2000(sample_lab, ref_lab)
        out_fibers[fiber] = {
            "sample_lab": {
                "L": round(sample_lab[0], 2),
                "a": round(sample_lab[1], 2),
                "b": round(sample_lab[2], 2),
            },
            "reference_lab": ref,
            "delta_e": round(delta_e, 3),
            "gray_scale_grade": map_delta_e_to_grade(delta_e, thresholds),
            "band_confidence": seg["band_confidence"].get(fiber),
        }

    return {
        "algorithm_version": ALGORITHM_VERSION,
        "fibers": out_fibers,
        "quality_flags": {
            "bands": len(fibers),
            "source": "auto-strip-detection",
            "orientation": seg["orientation"],
            "boundary_method": seg["boundary_method"],
            "bbox": seg["bbox"],
            "fill_ratio": seg["fill_ratio"],
            "colour_correction": colour_correction,
            "capture": quality,
        },
        "warnings": pipeline_warnings,
    }
