"""Geometric correction ONLY (homography). It does NOT neutralize light —
color correction is a separate step (see color_correction.py)."""

from __future__ import annotations

from typing import Any


def rectify_perspective(
    image: Any, marker_points: Any, output_size: tuple[int, int] = (1200, 800)
) -> Any:
    """Apply homography -> canonical layout. Implemented in Sprint 3."""
    raise NotImplementedError("vision.geometry — Sprint 3")
