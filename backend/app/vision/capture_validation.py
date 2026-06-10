"""Capture quality gate: blur, exposure, markers, tile, ROI, distance, tilt,
illuminant. iPhone sensors are a capture quality gate, NOT lab metrology."""

from __future__ import annotations

from typing import Any


def validate_capture(image: Any, telemetry: dict[str, Any]) -> dict[str, Any]:
    """Return quality flags + accept/reject. Implemented in Sprint 3."""
    raise NotImplementedError("vision.capture_validation — Sprint 3")
