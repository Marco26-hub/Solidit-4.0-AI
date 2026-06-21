"""Geometric correction ONLY (homography). It does NOT neutralize light —
colour correction is a separate step (see color_correction.py).

Given the four ArUco fiducials of the dima (markers.CORNER_IDS, ordered
TL→TR→BR→BL), we compute the perspective transform that maps the marker-centre
quadrilateral onto a canonical axis-aligned rectangle and warp the frame to it.
After rectification the strip sits in a known, tilt/rotation-free layout so band
segmentation no longer depends on the placement convention.
"""

from __future__ import annotations

from typing import Any

from app.vision.markers import CORNER_IDS


def order_corner_points(markers: dict[str, Any]) -> list[list[float]] | None:
    """Extract the four dima-corner centres in canonical TL→TR→BR→BL order.

    Returns None when the four CORNER_IDS are not all present."""
    centers = markers.get("centers") or {}
    if not all(cid in centers for cid in CORNER_IDS):
        return None
    return [list(centers[cid]) for cid in CORNER_IDS]


def rectify_perspective(
    image_rgb: Any,
    markers: dict[str, Any],
    output_size: tuple[int, int] = (1200, 800),
) -> dict[str, Any]:
    """Warp the frame to a canonical rectangle using the four corner fiducials.

    Args:
        image_rgb: HxWx3 RGB array.
        markers: result of markers.detect_markers (uses its corner centres).
        output_size: (width, height) of the rectified canvas.

    Returns:
        {
          "image": ndarray | None,   # rectified RGB, or None if not rectified
          "applied": bool,
          "method": "homography_aruco" | "none",
          "reason": str | None,      # why it was skipped, when applied is False
          "src_points": [[x,y]*4] | None,
        }

    Never raises for the "no fiducials" case — returns applied=False so the
    pipeline falls back to auto-strip-detection (a flagged, non-validated path).
    """
    src = order_corner_points(markers)
    if src is None:
        return _skipped("corner_markers_incomplete")

    try:
        import cv2
    except ImportError:
        return _skipped("opencv_missing")

    import numpy as np

    w, h = int(output_size[0]), int(output_size[1])
    src_pts = np.asarray(src, dtype=np.float32)
    dst_pts = np.asarray([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)
    transform = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(
        np.asarray(image_rgb)[:, :, :3].astype(np.uint8), transform, (w, h)
    )
    return {
        "image": warped,
        "applied": True,
        "method": "homography_aruco",
        "reason": None,
        "src_points": [[float(x), float(y)] for x, y in src],
    }


def _skipped(reason: str) -> dict[str, Any]:
    return {
        "image": None,
        "applied": False,
        "method": "none",
        "reason": reason,
        "src_points": None,
    }
