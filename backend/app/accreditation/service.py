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
    ProficiencyTest,
    QualityReport,
    ValidationRun,
)

MIN_VALIDATION_SAMPLES = 50  # spec target for pre-validation


def _item(key: str, label: str, status: str, detail: str) -> dict[str, str]:
    return {"key": key, "label": label, "status": status, "detail": detail}


def _build_readiness_items(
    *,
    valid_refs_count: int,
    method_docs_count: int,
    total_scored: int,
    best_pct: float,
    locked_reports_count: int,
    pt_ok_count: int,
    pt_total: int,
) -> list[dict[str, str]]:
    return [
        _item(
            "quality_manual",
            "Manuale qualità e dossier Accredia collegati",
            "done",
            "manuale, procedura, matrice evidenze e moduli operativi",
        ),
        _item("method", "Metodo definito e documentato (SOP)", "done", "Fascicolo + SOP 01-08"),
        _item(
            "hardware_gate",
            "Kit hardware obbligatorio in analisi",
            "done",
            "lightbox, white tile e grey scale vincolati dal software",
        ),
        _item("rls", "Multi-tenant + audit trail append-only", "done", "RLS + audit"),
        _item(
            "report_lock",
            "Report non modificabile dopo emissione",
            "done",
            "finalize/lock + SHA-256",
        ),
        _item(
            "evidence_matrix",
            "Matrice requisiti-evidenze disponibile",
            "done",
            "collega requisiti, SOP, moduli software e gap residui",
        ),
        _item(
            "uncertainty",
            "Motore incertezza e guard band",
            "partial",
            "software pronto; budget reale da compilare con dati validati",
        ),
        _item(
            "instruments",
            "Strumenti/riferimenti tarati e in validità",
            "done" if valid_refs_count else "todo",
            f"{valid_refs_count} riferimenti validi",
        ),
        _item(
            "norms",
            "Norme di riferimento caricate (copia licenziata)",
            "done" if method_docs_count else "todo",
            f"{method_docs_count} documenti",
        ),
        _item(
            "validation",
            f"Validazione metodo (≥{MIN_VALIDATION_SAMPLES} campioni, ≥90% entro ±0.5)",
            "done"
            if (total_scored >= MIN_VALIDATION_SAMPLES and best_pct >= 90)
            else ("partial" if total_scored else "todo"),
            f"{total_scored} campioni · miglior {best_pct}% entro ±0.5",
        ),
        _item(
            "reports",
            "Report ufficiali emessi (finalizzati)",
            "done" if locked_reports_count else "todo",
            f"{locked_reports_count} report bloccati",
        ),
        _item(
            "proficiency",
            "Prove interlaboratorio / PT (esito soddisfacente)",
            "done" if pt_ok_count else ("partial" if pt_total else "todo"),
            f"{pt_ok_count}/{pt_total} round soddisfacenti",
        ),
        # off-software (the lab/consultant must do these)
        _item(
            "grading_validated",
            "Profili grading validati/licenziati",
            "todo",
            "sostituire ESEMPIO",
        ),
        _item("operators", "Operatori formati e qualificati", "todo", "registro formazione"),
        _item("consultant", "Revisione consulente ISO/IEC 17025", "todo", "esterno"),
        _item("scope", "Metodo incluso nello scopo Accredia", "todo", "iter accreditamento"),
    ]


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

    pts = list(
        (
            await session.execute(
                select(ProficiencyTest).where(ProficiencyTest.company_id == company_id)
            )
        )
        .scalars()
        .all()
    )
    pt_ok = sum(1 for p in pts if p.verdict == "soddisfacente")

    items = _build_readiness_items(
        valid_refs_count=len(valid_refs),
        method_docs_count=method_docs,
        total_scored=total_scored,
        best_pct=best_pct,
        locked_reports_count=locked_reports,
        pt_ok_count=pt_ok,
        pt_total=len(pts),
    )

    done = sum(1 for i in items if i["status"] == "done")
    if done <= 6:
        level = "Prototipo / strumento interno"
    elif (
        best_pct >= 90
        and total_scored >= MIN_VALIDATION_SAMPLES
        and valid_refs
        and method_docs
        and locked_reports
    ):
        level = "Metodo pre-validato"
    else:
        level = "Tool interno (validazione in corso)"

    return {
        "level": level,
        "done": done,
        "total": len(items),
        "items": items,
    }
