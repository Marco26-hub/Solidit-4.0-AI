"""Color correction (3x3 matrix / optional LUT) from the reference card patches
under a controlled illuminant. SEPARATE from geometry. Matrix computation from a
ColorChecker is a calibration step; here we APPLY a stored matrix."""

from __future__ import annotations

from typing import Any


def compute_color_correction(image: Any, reference_patches: Any) -> Any:
    """Compute white-balance + 3x3 matrix from reference patches. Implemented in a
    calibration step (needs the ColorChecker layout); not in the base pipeline."""
    raise NotImplementedError("vision.color_correction.compute — calibration step")


def apply_color_matrix(image_rgb: Any, matrix_3x3: Any) -> Any:
    """Apply a stored 3x3 color-correction matrix to an RGB image (0..255)."""
    import numpy as np

    img = np.asarray(image_rgb, dtype=np.float64) / 255.0
    matrix = np.asarray(matrix_3x3, dtype=np.float64)
    corrected = np.clip(img @ matrix.T, 0.0, 1.0)
    return (corrected * 255.0).astype("uint8")
