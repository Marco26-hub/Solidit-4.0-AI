"""Vision engine (Sprint 3). Real Lab/ΔE/ROI/grading implemented; heavy libs
(numpy/scikit-image/Pillow/opencv) are LAZY-imported inside functions so the base
app installs without them. Install with: pip install -e ".[vision]".

Geometry (ArUco markers + homography, geometry.py/markers.py) is an OPTIONAL
pre-step: when the dima's four fiducials are present the frame is rectified to a
canonical layout; otherwise the pipeline falls back to auto-strip-detection (a
flagged, non-validated path) and splits the strip into per-fibre bands from the
selected profile. Geometry and colour correction stay SEPARATE.

Pipeline (from VISION_ENGINE_SPEC — geometry and color stay SEPARATE):
    raw image -> (capture validation) -> (ArUco homography, optional)
    -> color correction -> multifiber ROI split -> RGB to Lab
    -> ΔE CIEDE2000 vs reference
    -> configurable grey-scale staining grade -> (brand rule pass/fail in service)
"""

ALGORITHM_VERSION = "vision-core-0.3.0"
