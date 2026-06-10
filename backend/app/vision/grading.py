"""Configurable grey-scale staining mapping (ΔE -> grade 5..1).

CRITICAL: the thresholds below are a NON-proprietary EXAMPLE profile so the
pipeline is runnable. Do NOT treat them as an official ISO 105-A03 / AATCC table.
Each company loads a validated/licensed profile (see VISION_ENGINE_SPEC). Higher
ΔE (more staining) => lower grade."""

from __future__ import annotations

# Example only — replace with a validated profile per company/standard.
DEFAULT_STAINING_THRESHOLDS: list[dict] = [
    {"max_delta_e": 0.4, "grade": 5.0},
    {"max_delta_e": 1.25, "grade": 4.5},
    {"max_delta_e": 2.1, "grade": 4.0},
    {"max_delta_e": 2.95, "grade": 3.5},
    {"max_delta_e": 4.1, "grade": 3.0},
    {"max_delta_e": 5.8, "grade": 2.5},
    {"max_delta_e": 8.2, "grade": 2.0},
    {"max_delta_e": 11.6, "grade": 1.5},
]


def map_delta_e_to_grade(delta_e: float, thresholds: list[dict]) -> float:
    """Pure, config-driven mapping (no hardcoded standard tables)."""
    for row in sorted(thresholds, key=lambda r: r["max_delta_e"]):
        if delta_e <= row["max_delta_e"]:
            return float(row["grade"])
    return 1.0
