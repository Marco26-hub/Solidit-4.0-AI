"""Measurement-uncertainty budget for the digital-imaging colour measurand.

This follows the GUM / ISO/IEC 17025 §7.6 pattern used in laboratories:
convert each uncertainty source to a standard uncertainty ``u_i`` in ΔE units,
combine independent components in quadrature, estimate effective degrees of
freedom with Welch-Satterthwaite when possible, and report expanded uncertainty
``U = k * u_c``.

It is intentionally conservative and auditable. It does not magically accredit
the method; it creates the numeric budget the lab/consultant must validate with
real repeatability, reproducibility, reference and characterisation data.
"""

from __future__ import annotations

import math
import statistics
from typing import Any

_DEFAULT_COMPONENTS = ("repeatability", "characterisation", "reproducibility", "reference")
_DISTRIBUTION_DIVISOR = {
    "normal": 1.0,
    "rectangular": math.sqrt(3.0),
    "triangular": math.sqrt(6.0),
    "u_shaped": math.sqrt(2.0),
}

_NOTE = (
    "Budget GUM/ISO 17025 calcolato da componenti dichiarate dal laboratorio. "
    "Usare solo con dati reali di validazione del metodo; il budget e la regola "
    "decisionale devono essere approvati nel dossier di accreditamento."
)


def _coverage_from_degrees_of_freedom(
    effective_df: float | None, confidence: float
) -> tuple[float, str]:
    if not effective_df or not math.isfinite(effective_df) or effective_df <= 0:
        return 2.0, "fixed_k_2"
    try:
        from scipy.stats import t

        alpha = 1.0 - confidence
        return float(t.ppf(1.0 - alpha / 2.0, effective_df)), "student_t"
    except Exception:  # noqa: BLE001 - scipy may be absent in slim installs
        return 2.0, "fixed_k_2"


def _standard_uncertainty_from_component(component: dict[str, Any]) -> dict[str, Any]:
    name = str(component.get("component") or component.get("name") or "").strip()
    if not name:
        raise ValueError("component senza nome")

    distribution = str(component.get("distribution") or "normal").lower()
    if distribution not in _DISTRIBUTION_DIVISOR:
        raise ValueError(f"distribuzione non supportata per '{name}': {distribution}")

    observations = component.get("observations")
    if observations is not None:
        vals = [float(v) for v in observations if v is not None]
        if len(vals) < 2:
            raise ValueError(f"servono almeno 2 osservazioni per '{name}'")
        if any(v < 0 for v in vals):
            raise ValueError(f"osservazione negativa non valida per '{name}'")
        std = statistics.stdev(vals)
        use_mean = bool(component.get("use_mean", True))
        standard_uncertainty = std / math.sqrt(len(vals)) if use_mean else std
        degrees_freedom = len(vals) - 1
        source = "observations_mean" if use_mean else "observations_single"
        return {
            "component": name,
            "standard_uncertainty": standard_uncertainty,
            "degrees_freedom": degrees_freedom,
            "distribution": "normal",
            "source": source,
            "n": len(vals),
            "mean": statistics.mean(vals),
            "std_dev": std,
        }

    input_type = str(component.get("input_type") or "standard_uncertainty")
    raw_value = component.get("value", component.get("standard_uncertainty"))
    if raw_value is None:
        raise ValueError(f"valore mancante per '{name}'")
    value = float(raw_value)
    if value < 0:
        raise ValueError(f"incertezza negativa non valida per '{name}'")

    if input_type == "standard_uncertainty":
        standard_uncertainty = value
    elif input_type == "expanded_uncertainty":
        divisor = float(component.get("coverage_factor") or 2.0)
        if divisor <= 0:
            raise ValueError(f"coverage_factor non valido per '{name}'")
        standard_uncertainty = value / divisor
    elif input_type == "half_width":
        standard_uncertainty = value / _DISTRIBUTION_DIVISOR[distribution]
    elif input_type == "standard_deviation":
        n = component.get("n")
        if n is not None:
            n = int(n)
            if n < 2:
                raise ValueError(f"n deve essere >= 2 per '{name}'")
            standard_uncertainty = (
                value / math.sqrt(n) if component.get("use_mean", True) else value
            )
        else:
            standard_uncertainty = value
    else:
        raise ValueError(f"input_type non supportato per '{name}': {input_type}")

    degrees_freedom = component.get("degrees_freedom")
    if degrees_freedom is not None:
        degrees_freedom = float(degrees_freedom)
        if degrees_freedom <= 0:
            raise ValueError(f"degrees_freedom deve essere > 0 per '{name}'")

    return {
        "component": name,
        "standard_uncertainty": standard_uncertainty,
        "degrees_freedom": degrees_freedom,
        "distribution": distribution,
        "source": input_type,
    }


def _effective_degrees_of_freedom(rows: list[dict[str, Any]], u_c: float) -> float | None:
    if u_c <= 0:
        return None
    denom = 0.0
    has_df = False
    for row in rows:
        df = row.get("degrees_freedom")
        if df is None or not math.isfinite(float(df)):
            continue
        has_df = True
        u_i = float(row["standard_uncertainty"])
        denom += (u_i**4) / float(df)
    if not has_df or denom <= 0:
        return None
    return (u_c**4) / denom


def _decision_rule(
    measured_value: float | None,
    tolerance_limit: float | None,
    expanded_uncertainty: float,
    *,
    direction: str = "max",
) -> dict[str, Any] | None:
    if measured_value is None or tolerance_limit is None:
        return None
    measured = float(measured_value)
    limit = float(tolerance_limit)
    if direction not in ("max", "min"):
        raise ValueError("decision_direction deve essere 'max' o 'min'")
    if direction == "max":
        pass_guarded = measured + expanded_uncertainty <= limit
        fail_guarded = measured - expanded_uncertainty > limit
    else:
        pass_guarded = measured - expanded_uncertainty >= limit
        fail_guarded = measured + expanded_uncertainty < limit
    if pass_guarded:
        verdict = "pass"
    elif fail_guarded:
        verdict = "fail"
    else:
        verdict = "guard_band_inconclusive"
    return {
        "rule": "guard_band",
        "direction": direction,
        "measured_value": round(measured, 4),
        "tolerance_limit": round(limit, 4),
        "guard_band": round(expanded_uncertainty, 4),
        "verdict": verdict,
    }


def combine_uncertainty(
    components: dict[str, float | None] | list[dict[str, Any]],
    *,
    coverage_factor: float | None = 2.0,
    confidence_level: float = 0.95,
    measured_value: float | None = None,
    tolerance_limit: float | None = None,
    decision_direction: str = "max",
) -> dict[str, Any]:
    """Combine uncertainty components in ΔE units.

    Backward-compatible form: ``{"repeatability": 0.3, ...}`` means each value is
    already a standard uncertainty. Advanced form is a list of component dicts:
    ``{"component": "reference", "value": 0.6, "input_type": "half_width",
    "distribution": "rectangular"}``.
    """
    if coverage_factor is not None and coverage_factor <= 0:
        raise ValueError("coverage_factor deve essere > 0")
    if not 0.5 < confidence_level < 1.0:
        raise ValueError("confidence_level deve essere fra 0.5 e 1.0")

    if isinstance(components, dict):
        advanced = [
            {"component": name, "value": value, "input_type": "standard_uncertainty"}
            for name, value in components.items()
            if value is not None
        ]
    else:
        advanced = list(components)
    rows = [_standard_uncertainty_from_component(c) for c in advanced]
    rows = [r for r in rows if float(r["standard_uncertainty"]) >= 0]
    if not rows:
        raise ValueError("nessuna componente di incertezza fornita")

    u_c = math.sqrt(sum(float(row["standard_uncertainty"]) ** 2 for row in rows))
    effective_df = _effective_degrees_of_freedom(rows, u_c)
    if coverage_factor is None:
        coverage_factor, coverage_method = _coverage_from_degrees_of_freedom(
            effective_df, confidence_level
        )
    else:
        coverage_method = "user_supplied"
    expanded = float(coverage_factor) * u_c
    contributions = [
        {
            "component": row["component"],
            "standard_uncertainty": round(float(row["standard_uncertainty"]), 4),
            "distribution": row.get("distribution"),
            "source": row.get("source"),
            "degrees_freedom": round(float(row["degrees_freedom"]), 2)
            if row.get("degrees_freedom") is not None
            else None,
            "variance_share_pct": round(
                100.0 * (float(row["standard_uncertainty"]) ** 2) / (u_c * u_c), 1
            )
            if u_c > 0
            else 0.0,
        }
        for row in sorted(rows, key=lambda item: -float(item["standard_uncertainty"]))
    ]
    decision = _decision_rule(
        measured_value,
        tolerance_limit,
        expanded,
        direction=decision_direction,
    )
    return {
        "unit": "delta_e",
        "components": contributions,
        "combined_standard_uncertainty": round(u_c, 4),
        "effective_degrees_freedom": round(effective_df, 2) if effective_df else None,
        "coverage_factor": round(float(coverage_factor), 4),
        "coverage_method": coverage_method,
        "expanded_uncertainty": round(expanded, 4),
        "confidence_level": f"{round(confidence_level * 100, 2)}%",
        "decision_rule": decision,
        "dominant_component": contributions[0]["component"] if contributions else None,
        "note": _NOTE,
    }
