"""Accreditation-readiness checklist, computed from the live system state.

Mirrors the FASCICOLO_TECNICO checklist: each item is derived from data where the
software can know it (validation campaigns, calibration references, method docs,
locked reports) and marked informational where it depends on off-software actions
(real-sample study, consultant review, Accredia scope). NOT a declaration of
compliance — only a readiness snapshot to drive the work toward accreditation."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calibration.service import compute_validity
from app.db.models import (
    CalibrationReference,
    MethodDocument,
    QualityReport,
    ValidationRun,
)

MIN_VALIDATION_SAMPLES = 50  # spec target for pre-validation


async def readiness(session: AsyncSession, company_id: uuid.UUID) -> dict:
    runs = list(
        (await session.execute(select(ValidationRun).where(ValidationRun.company_id == company_id)))
        .scalars()
        .all()
    )
    computed = [r for r in runs if r.status == "computed"]
    best_pct = max(
        (float(r.metrics.get("pct_within_half_grade", 0) or 0) for r in computed), default=0.0
    )
    total_scored = sum(int(r.metrics.get("scored", 0) or 0) for r in computed)

    refs = list(
        (
            await session.execute(
                select(CalibrationReference).where(CalibrationReference.company_id == company_id)
            )
        )
        .scalars()
        .all()
    )
    valid_refs = [r for r in refs if compute_validity(r) in ("valid", "expiring")]

    method_docs = (
        await session.execute(
            select(func.count())
            .select_from(MethodDocument)
            .where(MethodDocument.company_id == company_id)
        )
    ).scalar_one()

    locked_reports = (
        await session.execute(
            select(func.count())
            .select_from(QualityReport)
            .where(QualityReport.company_id == company_id, QualityReport.status == "locked")
        )
    ).scalar_one()

    def item(key, label, status, detail):
        return {"key": key, "label": label, "status": status, "detail": detail}

    items = [
        item("method", "Metodo definito e documentato (SOP)", "done", "Fascicolo + SOP 01-08"),
        item("rls", "Multi-tenant + audit trail append-only", "done", "RLS + audit"),
        item(
            "report_lock",
            "Report non modificabile dopo emissione",
            "done",
            "finalize/lock + SHA-256",
        ),
        item(
            "instruments",
            "Strumenti/riferimenti tarati e in validità",
            "done" if valid_refs else "todo",
            f"{len(valid_refs)} riferimenti validi",
        ),
        item(
            "norms",
            "Norme di riferimento caricate (copia licenziata)",
            "done" if method_docs else "todo",
            f"{method_docs} documenti",
        ),
        item(
            "validation",
            f"Validazione metodo (≥{MIN_VALIDATION_SAMPLES} campioni, ≥90% entro ±0.5)",
            "done"
            if (total_scored >= MIN_VALIDATION_SAMPLES and best_pct >= 90)
            else ("partial" if total_scored else "todo"),
            f"{total_scored} campioni · miglior {best_pct}% entro ±0.5",
        ),
        item(
            "reports",
            "Report ufficiali emessi (finalizzati)",
            "done" if locked_reports else "todo",
            f"{locked_reports} report bloccati",
        ),
        # off-software (the lab/consultant must do these)
        item("uncertainty", "Incertezza stimata", "todo", "da redigere dopo validazione"),
        item(
            "grading_validated", "Profili grading validati/licenziati", "todo", "sostituire ESEMPIO"
        ),
        item("operators", "Operatori formati e qualificati", "todo", "registro formazione"),
        item("consultant", "Revisione consulente ISO/IEC 17025", "todo", "esterno"),
        item("scope", "Metodo incluso nello scopo Accredia", "todo", "iter accreditamento"),
    ]

    done = sum(1 for i in items if i["status"] == "done")
    if done <= 4:
        level = "Prototipo / strumento interno"
    elif best_pct >= 90 and total_scored >= MIN_VALIDATION_SAMPLES:
        level = "Metodo pre-validato"
    else:
        level = "Tool interno (validazione in corso)"

    return {
        "level": level,
        "done": done,
        "total": len(items),
        "items": items,
    }
