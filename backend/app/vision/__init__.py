"""Vision engine (Sprint 3). Real Lab/ΔE/ROI/grading implemented; heavy libs
(numpy/scikit-image/Pillow) are LAZY-imported inside functions so the base app
installs without them. Install with: pip install -e ".[vision]".

Geometry (homography) + markers (ArUco) need OpenCV and are a later hardening
step; the current pipeline assumes a cropped/canonical multifiber strip image
(guaranteed in practice by the physical dima) and splits it into per-fiber bands
driven by the selected strip profile.

Pipeline (from VISION_ENGINE_SPEC — geometry and color stay SEPARATE):
    raw image -> (capture validation) -> (homography*) -> color correction
    -> multifiber ROI split -> RGB to Lab -> ΔE CIEDE2000 vs reference
    -> configurable grey-scale staining grade -> (brand rule pass/fail in service)
    * not yet (needs OpenCV)
"""

ALGORITHM_VERSION = "vision-core-0.2.0"
