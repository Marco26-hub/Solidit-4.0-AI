"""Pluggable spectral-estimation backend selection + result extraction.

Backends (all return STIMATA, never a measurement):
  - ``smoothest`` — deterministic smoothest-metamer (app.vision.spectral), no GPU,
    no dataset, available now.
  - ``remote_ml`` — a learned model served over HTTP (e.g. an NVIDIA DGX Spark
    box) at ``settings.spectral_inference_url``. Forward-wired; "unavailable"
    until the endpoint is configured. Needs a real spectrophotometer-paired
    dataset to be meaningful — still STIMATA, never accredited.
The factory falls back to ``smoothest`` (with a flag) when ``remote_ml`` is
selected but not reachable, so the feature always degrades gracefully.
"""

from __future__ import annotations

import uuid
from typing import Any, Protocol

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError, NotFoundError
from app.config import settings
from app.db.models import MeasurementResult
from app.vision.spectral import (
    DISCLAIMER,
    ESTIMATE_LABEL,
    SUPPORTED_ILLUMINANTS,
    estimate_reflectance,
)


class SpectralEstimator(Protocol):
    name: str

    def available(self) -> bool: ...

    def estimate(self, lab: list[float], *, illuminant: str, observer: str) -> dict[str, Any]: ...


class SmoothestMetamerEstimator:
    name = "smoothest"

    def available(self) -> bool:
        return True

    def estimate(self, lab: list[float], *, illuminant: str, observer: str) -> dict[str, Any]:
        return estimate_reflectance(lab, illuminant=illuminant, observer=observer)


class RemoteMLEstimator:
    """Learned RGB/Lab->reflectance model served over HTTP (NVIDIA Spark, later).

    The contract: POST {lab, illuminant, observer} -> a ReflectanceEstimate-shaped
    JSON with estimate=True/label="STIMATA". Kept here so wiring the Spark box is a
    config change, not a code change. Unavailable (and never used) until the URL
    is set.
    """

    name = "remote_ml"

    def __init__(self, url: str | None) -> None:
        self._url = url

    def available(self) -> bool:
        return bool(self._url)

    def estimate(self, lab: list[float], *, illuminant: str, observer: str) -> dict[str, Any]:
        if not self._url:
            raise AppError(
                "Backend ML non configurato (SPECTRAL_INFERENCE_URL assente).",
                code="spectral_backend_unavailable",
            )
        import httpx

        resp = httpx.post(
            self._url.rstrip("/") + "/estimate",
            json={"lab": lab, "illuminant": illuminant, "observer": observer},
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        # The remote model is UNTRUSTED for honesty: it only supplies the curve.
        # Every honesty-load-bearing field (rule 7) is authored locally so a remote
        # box can never relabel an estimate as a measurement, nor swap the
        # disclaimer. Force, never setdefault.
        data["estimate"] = True
        data["not_a_measurement"] = True
        data["label"] = ESTIMATE_LABEL
        data["engine"] = "remote_ml"
        data["disclaimer"] = DISCLAIMER
        return data


def get_estimator() -> tuple[SpectralEstimator, str | None]:
    """Return (estimator, fallback_reason). Honours settings.spectral_backend and
    degrades to smoothest when the remote model is selected but unreachable."""
    smoothest = SmoothestMetamerEstimator()
    if settings.spectral_backend == "remote_ml":
        remote = RemoteMLEstimator(settings.spectral_inference_url)
        if remote.available():
            return remote, None
        return smoothest, "remote_ml selezionato ma SPECTRAL_INFERENCE_URL assente"
    return smoothest, None


def estimate_lab(
    lab: list[float], *, illuminant: str = "D65", observer: str = "2"
) -> dict[str, Any]:
    if illuminant.upper() not in SUPPORTED_ILLUMINANTS:
        raise AppError(
            f"Illuminante non supportato: {illuminant}. Usa: {', '.join(SUPPORTED_ILLUMINANTS)}.",
            code="unsupported_illuminant",
        )
    estimator, fallback = get_estimator()
    out = estimator.estimate(lab, illuminant=illuminant.upper(), observer=observer)
    if fallback:
        out.setdefault("warnings", []).append(f"backend: {fallback} → uso metamero liscio")
    return out


_NOTE = (
    "Stime spettrali (R&D) per i Lab misurati. Sono STIMATE, non misure, e non "
    "fanno parte del report sigillato."
)


def _extract_fiber_labs(result: MeasurementResult) -> list[tuple[str, list[float]]]:
    """Pull per-fibre sample CIELAB out of a measurement result's vision payload."""
    res = result.results or {}
    vision = res.get("vision", {}) if isinstance(res, dict) else {}
    out: list[tuple[str, list[float]]] = []
    fibers = vision.get("fibers") if isinstance(vision, dict) else None
    if isinstance(fibers, dict):
        for fiber, data in fibers.items():
            lab = (data or {}).get("sample_lab")
            if isinstance(lab, dict) and {"L", "a", "b"} <= set(lab):
                out.append((fiber, [float(lab["L"]), float(lab["a"]), float(lab["b"])]))
    # colour-change single-sample shape
    single = vision.get("sample_lab") if isinstance(vision, dict) else None
    if isinstance(single, dict) and {"L", "a", "b"} <= set(single):
        out.append(("fabric", [float(single["L"]), float(single["a"]), float(single["b"])]))
    return out


async def estimate_for_result(
    session: AsyncSession,
    company_id: uuid.UUID,
    result_id: uuid.UUID,
    *,
    illuminant: str = "D65",
) -> dict[str, Any]:
    result = (
        await session.execute(
            select(MeasurementResult).where(
                MeasurementResult.id == result_id,
                MeasurementResult.company_id == company_id,
            )
        )
    ).scalar_one_or_none()
    if result is None:
        raise NotFoundError("Risultato di misura non trovato")

    fiber_labs = _extract_fiber_labs(result)

    def _estimate_all() -> list[dict[str, Any]]:
        # may hit a remote model (sync httpx) — run off the event loop
        return [
            {"fiber": f, "sample_lab": lab, "estimate": estimate_lab(lab, illuminant=illuminant)}
            for f, lab in fiber_labs
        ]

    fibers = await run_in_threadpool(_estimate_all)
    return {
        "measurement_result_id": str(result_id),
        "label": ESTIMATE_LABEL,
        "disclaimer": DISCLAIMER,
        "note": _NOTE,
        "fibers": fibers,
    }
