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
    grey_scale: bool = False,
    white_reference_lab: list[float] | None = None,
    geometry_markers: bool = False,
) -> dict[str, Any]:
    """fibers: ordered fibre codes (from the strip profile).
    reference_lab: {fiber: {"L":..,"a":..,"b":..}} — the unstained reference.
    grey_scale: when True, look for an in-frame neutral reference and white-balance
    the image with it (ISO 105-A11 in-frame colour correction).
    white_reference_lab: certified CIELAB of the in-frame white tile — when given,
    the correction anchors to it (traceable) instead of self-neutralising.
    geometry_markers: when True, look for the dima's four ArUco fiducials and
    rectify the frame via homography BEFORE colour correction (geometry stays
    separate from colour). Falls back to auto-strip-detection (flagged) if the
    markers are absent."""
    import numpy as np
    from PIL import Image

    thresholds = thresholds or DEFAULT_STAINING_THRESHOLDS
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    arr: Any = np.asarray(image)
    pipeline_warnings: list[str] = []
    grey_flags: dict[str, Any] = {"requested": grey_scale, "detected": False}

    # GEOMETRY first (separate from colour): rectify via ArUco homography if asked.
    geometry_flags: dict[str, Any] = {
        "requested": geometry_markers,
        "method": "auto-strip-detection",
        "rectified": False,
    }
    if geometry_markers:
        from app.vision.geometry import rectify_perspective
        from app.vision.markers import detect_markers

        markers = detect_markers(arr)
        geometry_flags["markers_found"] = markers["found"]
        rect = rectify_perspective(arr, markers)
        if rect["applied"]:
            arr = rect["image"]
            geometry_flags.update(
                method="homography_aruco", rectified=True, src_points=rect["src_points"]
            )
        else:
            geometry_flags["fallback_reason"] = rect["reason"]
            pipeline_warnings.append(
                "geometry: marker ArUco richiesti ma rettifica NON applicata "
                f"({rect['reason']}) — uso auto-rilevamento striscia (non validato)"
            )

    # precedence: explicit device matrix > in-frame grey-scale > none
    if color_matrix is not None:
        arr = apply_color_matrix(arr, color_matrix)
        colour_correction = "device_matrix"
    elif grey_scale:
        from app.vision.grey_scale import (
            find_neutral_reference,
            neutral_white_balance,
            white_balance_to_certified,
        )

        # with a certified white we anchor by BRIGHTNESS (the tile may read
        # off-neutral under a colour cast); without it we require true neutrality
        ref = find_neutral_reference(
            arr, max_chroma_ratio=0.4 if white_reference_lab is not None else 0.06
        )
        if ref is not None:
            if white_reference_lab is not None:
                arr = white_balance_to_certified(arr, ref["rgb"], white_reference_lab)
                colour_correction = "in_frame_certified_white"
                grey_flags.update(detected=True, reference=ref, certified_lab=white_reference_lab)
            else:
                arr = neutral_white_balance(arr, ref["rgb"])
                colour_correction = "in_frame_grey_scale"
                grey_flags.update(detected=True, reference=ref)
        else:
            colour_correction = "none"
            pipeline_warnings.append(
                "grey_scale: riferimento neutro richiesto ma NON rilevato nel fotogramma"
            )
    else:
        colour_correction = "none"

    seg = detect_and_split(arr, fibers)
    rois = seg["rois"]
    quality = assess_capture(arr, fill_ratio=seg.get("fill_ratio"))

    pipeline_warnings += list(quality["warnings"])
    if colour_correction == "none":
        pipeline_warnings.append(
            "colour_correction: non applicata (RGB camera grezzo, nessuna taratura/grey-scale)"
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
            "geometry": geometry_flags,
            "orientation": seg["orientation"],
            "boundary_method": seg["boundary_method"],
            "bbox": seg["bbox"],
            "fill_ratio": seg["fill_ratio"],
            "colour_correction": colour_correction,
            "grey_scale": grey_flags,
            "capture": quality,
        },
        "warnings": pipeline_warnings,
    }
