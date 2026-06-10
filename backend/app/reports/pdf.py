"""Render a Digital Quality Report PDF (ReportLab). Embeds the data, the SHA-256
integrity seal and a QR code linking to the verify endpoint.

Positioning (per CLAUDE.md / SECURITY): the SHA-256 is a *cryptographic integrity
seal*, NOT a qualified digital signature; the report supports the lab, it does not
replace an accredited laboratory nor auto-certify to ISO."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DISCLAIMER = (
    "Report Digitale di Controllo Qualità Tessile a supporto del laboratorio. "
    "Il codice SHA-256 è un sigillo tecnico di integrità del documento, NON una firma "
    "digitale qualificata. La piattaforma digitalizza e standardizza il controllo qualità; "
    "non sostituisce un laboratorio accreditato né certifica automaticamente secondo ISO. "
    "La validità come certificazione dipende dal protocollo aziendale e dalla validazione "
    "del responsabile qualità."
)


def _qr(verify_url: str, size_mm: float = 32) -> Drawing:
    widget = QrCodeWidget(verify_url)
    bounds = widget.getBounds()
    w = bounds[2] - bounds[0]
    h = bounds[3] - bounds[1]
    side = size_mm * mm
    drawing = Drawing(side, side, transform=[side / w, 0, 0, side / h, 0, 0])
    drawing.add(widget)
    return drawing


def build_report_pdf(payload: dict[str, Any], sha256_hash: str, verify_url: str) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        title=payload.get("report_number", "report"),
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    small = ParagraphStyle(
        "small", parent=styles["Normal"], fontSize=7.5, textColor=colors.HexColor("#475569")
    )

    job = payload.get("test_job", {})
    brand = payload.get("brand") or {}
    pass_fail = payload.get("measurement", {}).get("pass_fail", {})
    overall = pass_fail.get("overall_pass")
    evaluated = pass_fail.get("evaluated")

    story: list[Any] = [
        Paragraph("Digital Quality Report", styles["Title"]),
        Paragraph("Solidità 4.0 — Controllo Qualità Tessile", styles["Normal"]),
        Spacer(1, 8),
    ]

    meta = [
        ["Report N.", payload.get("report_number", "-")],
        ["Azienda", payload.get("company", {}).get("name", "-")],
        ["Generato", payload.get("generated_at", "-")],
        ["Metodo", payload.get("test_method_code") or "-"],
        ["Brand", brand.get("name", "-")],
        ["Articolo", job.get("article_code") or "-"],
        ["Lotto", job.get("lot_code") or "-"],
        ["Barcode", job.get("barcode") or "-"],
    ]
    meta_table = Table(meta, colWidths=[35 * mm, 130 * mm])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
            ]
        )
    )
    story += [meta_table, Spacer(1, 10), Paragraph("Risultati", styles["Heading2"])]

    rows = [["Fibra", "Metrica", "Valore", "Limite", "Esito"]]
    fail_cells: list[int] = []
    for fiber, info in pass_fail.get("per_fiber", {}).items():
        checks = info.get("checks", [])
        if not checks:
            rows.append([fiber, "-", "-", "-", "PASS" if info.get("pass") else "FAIL"])
            if not info.get("pass"):
                fail_cells.append(len(rows) - 1)
            continue
        for chk in checks:
            rows.append(
                [
                    fiber,
                    chk.get("metric", "-"),
                    str(chk.get("value", "-")),
                    str(chk.get("limit", "-")),
                    "PASS" if chk.get("ok") else "FAIL",
                ]
            )
            if not chk.get("ok"):
                fail_cells.append(len(rows) - 1)

    results_table = Table(rows, colWidths=[35 * mm, 45 * mm, 30 * mm, 30 * mm, 25 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]
    for r in fail_cells:
        style.append(("TEXTCOLOR", (4, r), (4, r), colors.HexColor("#b91c1c")))
    results_table.setStyle(TableStyle(style))

    if evaluated:
        verdict = "PASS" if overall else "FAIL"
        color = "#15803d" if overall else "#b91c1c"
    else:
        verdict = "INCONCLUSIVE (nessuna regola brand applicabile)"
        color = "#a16207"
    verdict_style = ParagraphStyle(
        "verdict", parent=styles["Heading2"], textColor=colors.HexColor(color)
    )

    story += [
        results_table,
        Spacer(1, 8),
        Paragraph(f"Esito complessivo: {verdict}", verdict_style),
        Paragraph(
            f"Algoritmo: {payload.get('measurement', {}).get('algorithm_version', '-')}", small
        ),
        Spacer(1, 10),
        _qr(verify_url),
        Spacer(1, 4),
        Paragraph(f"SHA-256 (sigillo di integrità): {sha256_hash}", small),
        Paragraph(f"Verifica online: {verify_url}", small),
        Spacer(1, 10),
        Paragraph(DISCLAIMER, small),
    ]

    doc.build(story)
    return buf.getvalue()
