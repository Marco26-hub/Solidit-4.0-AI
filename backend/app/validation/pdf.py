"""Validation report PDF — the method-validation credibility document.

Original lab document (no copyrighted standard text): campaign identity, the
software-vs-reference samples, the computed statistics and an indicative verdict,
with the mandatory positioning disclaimer. Reviewed by the quality manager / an
ISO/IEC 17025 consultant; accreditation is granted by the accreditation body, not
produced by this software."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DISCLAIMER = (
    "Documento di validazione del metodo digitale di imaging per la valutazione "
    "assistita della solidità colore. Confronto del software rispetto a un metodo di "
    "riferimento (spettrofotometro / valutazione esperta / laboratorio). NON costituisce "
    "accreditamento: l'inserimento del metodo nello scopo di accreditamento è concesso "
    "dall'organismo di accreditamento previa validazione, procedura, incertezza e revisione "
    "di un consulente ISO/IEC 17025."
)


def build_validation_pdf(
    *, run_name: str, company_name: str, samples: list[dict], metrics: dict[str, Any]
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm, title=f"Validazione — {run_name}",
    )
    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, leading=11)
    story: list[Any] = [
        Paragraph("Report di validazione del metodo", styles["Title"]),
        Paragraph(f"Campagna: <b>{run_name}</b>", styles["Normal"]),
        Paragraph(f"Laboratorio: {company_name}", small),
        Spacer(1, 10),
        Paragraph("Statistiche", styles["Heading2"]),
    ]

    pass_txt = "PASS indicativo" if metrics.get("indicative_pass") else "SOTTO SOGLIA"
    rows = [
        ["Campioni valutati", str(metrics.get("scored", 0))],
        ["% entro ±0.5 grado", f"{metrics.get('pct_within_half_grade', '-')}%"],
        ["Scarto medio assoluto", str(metrics.get("mean_abs_grade_dev", "-"))],
        ["Bias (sistematico)", str(metrics.get("bias", "-"))],
        ["RMSE", str(metrics.get("rmse", "-"))],
        ["Scarto massimo", str(metrics.get("max_abs_grade_dev", "-"))],
        ["Soglia accettazione", f"{metrics.get('acceptance_threshold_pct', 90)}%"],
        ["Esito indicativo", pass_txt],
    ]
    t = Table(rows, colWidths=[70 * mm, 90 * mm])
    t.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story += [t, Spacer(1, 12), Paragraph("Campioni", styles["Heading2"])]

    head = ["Campione", "Fibra", "Riferimento", "Software", "Rif.", "|scarto|"]
    body = [head]
    for s in samples:
        sw, rf = s.get("software_grade"), s.get("reference_grade")
        dev = abs(float(sw) - float(rf)) if sw is not None and rf is not None else None
        body.append(
            [
                s.get("sample_code", ""),
                s.get("fiber") or "—",
                s.get("reference_method", ""),
                "—" if sw is None else f"{sw}",
                "—" if rf is None else f"{rf}",
                "—" if dev is None else f"{dev:.1f}",
            ]
        )
    st = Table(body, repeatRows=1)
    st.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ]
        )
    )
    story += [
        st,
        Spacer(1, 14),
        Paragraph("Disclaimer", styles["Heading2"]),
        Paragraph(DISCLAIMER, small),
    ]
    doc.build(story)
    return buf.getvalue()
