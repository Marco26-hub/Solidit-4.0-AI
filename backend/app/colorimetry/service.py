"""Thin service layer over the characterisation + uncertainty engines."""

from __future__ import annotations

from typing import Any

from app.common.errors import AppError
from app.vision.characterization import (
    apply_camera_transform,
    fit_camera_transform,
)
from app.vision.uncertainty import combine_uncertainty


def characterize(
    patches: list[list[float]],
    *,
    degree: int = 2,
    reference_lab: list[list[float]] | None = None,
) -> dict[str, Any]:
    try:
        return fit_camera_transform(patches, degree=degree, reference_lab=reference_lab)
    except ValueError as exc:
        raise AppError(str(exc), code="characterization_invalid") from exc


def apply(matrix: list[list[float]], rgb: list[float], *, degree: int = 2) -> dict[str, Any]:
    try:
        return apply_camera_transform(matrix, rgb, degree=degree)
    except (ValueError, IndexError) as exc:
        raise AppError(str(exc), code="apply_invalid") from exc


def uncertainty(
    components: dict[str, float | None] | list[dict[str, Any]],
    *,
    coverage_factor: float | None = 2.0,
    confidence_level: float = 0.95,
    measured_value: float | None = None,
    tolerance_limit: float | None = None,
    decision_direction: str = "max",
) -> dict[str, Any]:
    try:
        return combine_uncertainty(
            components,
            coverage_factor=coverage_factor,
            confidence_level=confidence_level,
            measured_value=measured_value,
            tolerance_limit=tolerance_limit,
            decision_direction=decision_direction,
        )
    except ValueError as exc:
        raise AppError(str(exc), code="uncertainty_invalid") from exc
