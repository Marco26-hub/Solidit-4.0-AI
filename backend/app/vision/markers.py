"""Fiducial marker detection (ArUco) for known reference points.

The hardware dima carries four ArUco markers, one per corner of the strip
window, with fixed IDs:

    id 0 = top-left, id 1 = top-right, id 2 = bottom-right, id 3 = bottom-left

Detecting them lets us compute a homography (see geometry.py) that rectifies the
strip to a canonical layout regardless of how the phone was tilted/rotated. This
is GEOMETRY ONLY — it never touches colour (rule: geometry and colour correction
stay separate). OpenCV is a lazy import so the base app installs without it.
"""

from __future__ import annotations

from typing import Any

# Dima corner convention. Order matters: it defines the canonical TL→TR→BR→BL
# mapping used by the homography.
CORNER_IDS: tuple[int, int, int, int] = (0, 1, 2, 3)
ARUCO_DICTIONARY = "DICT_4X4_50"


def detect_markers(image_rgb: Any) -> dict[str, Any]:
    """Detect ArUco markers in an RGB image.

    Returns:
        {
          "found": int,                       # how many markers detected
          "ids": [int, ...],                  # detected ids (sorted)
          "centers": {id: [x, y]},            # marker centroids (image pixels)
          "corners": {id: [[x,y]*4]},         # the four corners per marker
          "dictionary": "DICT_4X4_50",
          "has_corner_quad": bool,            # all four CORNER_IDS present
        }

    No exception when OpenCV is missing or nothing is found — callers treat an
    empty result as "no fiducials, fall back to auto-strip-detection".
    """
    try:
        import cv2  # lazy: only needed for marker/geometry hardening
    except ImportError:
        return _empty("opencv_missing")

    import numpy as np

    arr = np.asarray(image_rgb)
    if arr.ndim == 3 and arr.shape[2] >= 3:
        gray = cv2.cvtColor(arr[:, :, :3].astype(np.uint8), cv2.COLOR_RGB2GRAY)
    else:
        gray = arr.astype(np.uint8)

    dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, ARUCO_DICTIONARY))
    detector = cv2.aruco.ArucoDetector(dictionary, cv2.aruco.DetectorParameters())
    corners, ids, _rejected = detector.detectMarkers(gray)

    if ids is None or len(ids) == 0:
        return _empty("none_detected")

    centers: dict[int, list[float]] = {}
    corner_map: dict[int, list[list[float]]] = {}
    for marker_corners, marker_id in zip(corners, ids.flatten(), strict=False):
        mid = int(marker_id)
        quad = marker_corners.reshape(-1, 2)
        corner_map[mid] = [[float(x), float(y)] for x, y in quad]
        centers[mid] = [float(quad[:, 0].mean()), float(quad[:, 1].mean())]

    detected_ids = sorted(centers)
    return {
        "found": len(detected_ids),
        "ids": detected_ids,
        "centers": centers,
        "corners": corner_map,
        "dictionary": ARUCO_DICTIONARY,
        "has_corner_quad": all(cid in centers for cid in CORNER_IDS),
        "reason": None,
    }


def _empty(reason: str) -> dict[str, Any]:
    return {
        "found": 0,
        "ids": [],
        "centers": {},
        "corners": {},
        "dictionary": ARUCO_DICTIONARY,
        "has_corner_quad": False,
        "reason": reason,
    }
