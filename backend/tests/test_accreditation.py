from __future__ import annotations

from app.accreditation.service import _build_readiness_items


def test_readiness_items_connect_accreditation_dossier():
    items = _build_readiness_items(
        valid_refs_count=0,
        method_docs_count=0,
        total_scored=0,
        best_pct=0,
        locked_reports_count=0,
        pt_ok_count=0,
        pt_total=0,
    )
    by_key = {item["key"]: item for item in items}

    assert by_key["quality_manual"]["status"] == "done"
    assert by_key["evidence_matrix"]["status"] == "done"
    assert by_key["hardware_gate"]["status"] == "done"
    assert by_key["uncertainty"]["status"] == "partial"
    assert "budget reale" in by_key["uncertainty"]["detail"]


def test_readiness_items_mark_prevalidation_dependencies_done():
    items = _build_readiness_items(
        valid_refs_count=3,
        method_docs_count=2,
        total_scored=60,
        best_pct=92.5,
        locked_reports_count=4,
        pt_ok_count=1,
        pt_total=1,
    )
    by_key = {item["key"]: item for item in items}

    assert by_key["instruments"]["status"] == "done"
    assert by_key["norms"]["status"] == "done"
    assert by_key["validation"]["status"] == "done"
    assert by_key["reports"]["status"] == "done"
    assert by_key["proficiency"]["status"] == "done"
