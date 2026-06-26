from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.acroform import AcroForm
from reportlab.pdfgen.canvas import Canvas

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, BooleanObject, DictionaryObject, NameObject
except Exception:  # pragma: no cover - generation still works without pypdf
    PdfReader = None
    PdfWriter = None
    ArrayObject = None
    DictionaryObject = None
    BooleanObject = None
    NameObject = None


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "pdf" / "accredia"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X = 42
TOP_Y = PAGE_HEIGHT - 44
BOTTOM_Y = 42
LABEL_WIDTH = 165
FIELD_HEIGHT = 18
ROW_GAP = 8
SECTION_GAP = 14
FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


@dataclass(frozen=True)
class Field:
    label: str
    name: str
    height: int = FIELD_HEIGHT
    multiline: bool = False
    value: str = ""


@dataclass(frozen=True)
class TableField:
    label: str
    columns: tuple[str, ...]
    rows: tuple[str, ...]
    name_prefix: str
    first_column_editable: bool = False


@dataclass(frozen=True)
class Section:
    title: str
    fields: tuple[Field | TableField, ...]


@dataclass(frozen=True)
class FormDefinition:
    code: str
    title: str
    subtitle: str
    sections: tuple[Section, ...]


FORMS: tuple[FormDefinition, ...] = (
    FormDefinition(
        code="MOD-01",
        title="Piano validazione metodo",
        subtitle="Definisce perimetro, campioni, riferimenti e criteri di accettazione.",
        sections=(
            Section(
                "Identificazione",
                (
                    Field("Codice piano", "codice_piano"),
                    Field("Metodo/prova", "metodo_prova"),
                    Field("Versione software", "versione_software"),
                    Field("Versione algoritmo", "versione_algoritmo"),
                    Field("Kit hardware / seriali", "kit_hardware"),
                    Field("Profilo grading", "profilo_grading"),
                    Field("Responsabile tecnico", "responsabile_tecnico"),
                    Field("Data approvazione", "data_approvazione"),
                ),
            ),
            Section(
                "Disegno sperimentale",
                (
                    Field("Numero campioni", "numero_campioni"),
                    Field("Tipologie tessili", "tipologie_tessili", multiline=True, height=38),
                    Field("Fibre incluse", "fibre_incluse"),
                    Field("Range colori", "range_colori"),
                    Field("Metodo riferimento", "metodo_riferimento"),
                    Field("Numero repliche", "numero_repliche"),
                    Field("Operatori coinvolti", "operatori_coinvolti"),
                    Field("Condizioni ambientali", "condizioni_ambientali", multiline=True, height=38),
                ),
            ),
            Section(
                "Criteri di accettazione",
                (
                    TableField(
                        "Metriche",
                        ("Metrica", "Criterio"),
                        (
                            "Accuratezza grado",
                            "Bias",
                            "RMSE",
                            "Ripetibilita",
                            "Riproducibilita",
                            "Robustezza",
                            "Tasso rigetto quality gate",
                        ),
                        "criterio",
                    ),
                ),
            ),
        ),
    ),
    FormDefinition(
        code="MOD-02",
        title="Rapporto validazione metodo",
        subtitle="Raccoglie risultati, deviazioni, limiti e conclusione tecnica.",
        sections=(
            Section(
                "Identificazione",
                (
                    Field("Codice rapporto", "codice_rapporto"),
                    Field("Piano collegato", "piano_collegato"),
                    Field("Dataset", "dataset"),
                    Field("Data inizio/fine", "data_periodo"),
                    Field("Versione software", "versione_software"),
                    Field("Esito finale", "esito_finale"),
                ),
            ),
            Section(
                "Risultati",
                (
                    TableField(
                        "Metriche",
                        ("Metrica", "Risultato", "Criterio", "Esito"),
                        (
                            "Campioni validi",
                            "% entro +/-0,5 grado",
                            "Bias medio",
                            "RMSE",
                            "Scarto massimo repliche",
                            "Robustezza",
                        ),
                        "risultato",
                    ),
                ),
            ),
            Section(
                "Conclusione tecnica",
                (
                    Field("Limiti del metodo", "limiti_metodo", multiline=True, height=48),
                    Field("Condizioni obbligatorie di uso", "condizioni_uso", multiline=True, height=48),
                    Field("Casi esclusi", "casi_esclusi", multiline=True, height=40),
                    Field("Azioni correttive richieste", "azioni_correttive", multiline=True, height=40),
                    Field("Approvazione responsabile tecnico", "approvazione_responsabile"),
                ),
            ),
        ),
    ),
    FormDefinition(
        code="MOD-03",
        title="Budget incertezza",
        subtitle="Template GUM per contributi Type A/B, incertezza estesa e guard band.",
        sections=(
            Section(
                "Identificazione",
                (
                    Field("Metodo/prova", "metodo_prova"),
                    Field("Grandezza/risultato", "grandezza_risultato"),
                    Field("Unita", "unita"),
                    Field("Regola decisionale", "regola_decisionale"),
                    Field("Livello confidenza", "livello_confidenza"),
                ),
            ),
            Section(
                "Contributi di incertezza",
                (
                    TableField(
                        "Contributi",
                        (
                            "Contributo",
                            "Tipo",
                            "Distribuzione",
                            "Valore",
                            "Divisore",
                            "Sensibilita",
                            "u standard",
                        ),
                        (
                            "Ripetibilita",
                            "Riferimento colore",
                            "Lightbox / illuminazione",
                            "Geometria / ROI",
                            "Modello RGB-Lab",
                            "Profilo grading",
                        ),
                        "incertezza",
                    ),
                ),
            ),
            Section(
                "Risultato",
                (
                    Field("Incertezza combinata uc", "uc"),
                    Field("Gradi liberta effettivi", "gradi_liberta"),
                    Field("Fattore copertura k", "fattore_k"),
                    Field("Incertezza estesa U", "incertezza_estesa"),
                    Field("Guard band", "guard_band"),
                    Field("Approvazione metrologica", "approvazione_metrologica"),
                ),
            ),
        ),
    ),
    FormDefinition(
        code="MOD-04",
        title="Registro rischi e imparzialita",
        subtitle="Rischi tecnici, commerciali, metrologici e cybersecurity.",
        sections=(
            Section(
                "Registro rischi",
                (
                    TableField(
                        "Rischi",
                        (
                            "ID",
                            "Rischio",
                            "Area",
                            "Prob.",
                            "Impatto",
                            "Controllo",
                            "Responsabile",
                            "Stato",
                        ),
                        ("R-001", "R-002", "R-003", "R-004", "R-005", "R-006"),
                        "rischio",
                    ),
                ),
            ),
            Section(
                "Decisioni",
                (
                    Field("Rischi non accettabili", "rischi_non_accettabili", multiline=True, height=54),
                    Field("Azioni prioritarie", "azioni_prioritarie", multiline=True, height=54),
                    Field("Approvazione direzione", "approvazione_direzione"),
                ),
            ),
        ),
    ),
    FormDefinition(
        code="MOD-05",
        title="Checklist audit interno",
        subtitle="Checklist per audit interno prima della domanda o estensione.",
        sections=(
            Section(
                "Dati audit",
                (
                    Field("Codice audit", "codice_audit"),
                    Field("Data audit", "data_audit"),
                    Field("Auditor", "auditor"),
                    Field("Area auditata", "area_auditata"),
                ),
            ),
            Section(
                "Checklist",
                (
                    TableField(
                        "Domande",
                        ("Area", "Domanda audit", "Evidenza", "Esito", "Rilievo"),
                        (
                            "Scopo",
                            "SOP",
                            "Strumenti",
                            "Metodo",
                            "Incertezza",
                            "Report",
                            "Dati",
                            "Personale",
                            "NC",
                        ),
                        "audit",
                    ),
                ),
            ),
            Section(
                "Sintesi",
                (
                    Field("Rilievi maggiori", "rilievi_maggiori", multiline=True, height=44),
                    Field("Rilievi minori", "rilievi_minori", multiline=True, height=44),
                    Field("Raccomandazioni", "raccomandazioni", multiline=True, height=44),
                    Field("Firma auditor", "firma_auditor"),
                ),
            ),
        ),
    ),
    FormDefinition(
        code="MOD-06",
        title="Verbale riesame direzione",
        subtitle="Decisione documentata su stato del sistema e domanda Accredia.",
        sections=(
            Section(
                "Dati riesame",
                (
                    Field("Data", "data"),
                    Field("Partecipanti", "partecipanti", multiline=True, height=36),
                    Field("Periodo riesaminato", "periodo_riesaminato"),
                    Field("Versione software riesaminata", "versione_software"),
                    Field("Decisione domanda Accredia", "decisione_domanda"),
                ),
            ),
            Section(
                "Input obbligatori",
                (
                    Field("Esito audit interno", "esito_audit", multiline=True, height=34),
                    Field("Stato azioni correttive", "stato_azioni", multiline=True, height=34),
                    Field("Stato validazione", "stato_validazione", multiline=True, height=34),
                    Field("Stato incertezza", "stato_incertezza", multiline=True, height=34),
                    Field("Esiti PT/ILC", "esiti_pt_ilc", multiline=True, height=34),
                    Field("Reclami/non conformita", "reclami_nc", multiline=True, height=34),
                    Field("Risorse necessarie", "risorse_necessarie", multiline=True, height=34),
                    Field("Rischi residui", "rischi_residui", multiline=True, height=34),
                ),
            ),
            Section(
                "Decisioni",
                (
                    TableField(
                        "Decisioni",
                        ("Decisione", "Responsabile", "Scadenza"),
                        ("1", "2", "3", "4"),
                        "decisione",
                        True,
                    ),
                    Field("Approvazione direzione", "approvazione_direzione"),
                ),
            ),
        ),
    ),
    FormDefinition(
        code="MOD-07",
        title="Checklist freeze release accreditabile",
        subtitle="Controlli prima di usare una release in validazione o dossier.",
        sections=(
            Section(
                "Release",
                (
                    Field("Versione release", "versione_release"),
                    Field("Tag Git", "tag_git"),
                    Field("Commit hash", "commit_hash"),
                    Field("Data freeze", "data_freeze"),
                    Field("Responsabile software", "responsabile_software"),
                ),
            ),
            Section(
                "Controlli",
                (
                    TableField(
                        "Checklist",
                        ("Controllo", "Esito", "Evidenza"),
                        (
                            "Tag Git creato",
                            "Migrazioni database applicate",
                            "Test backend superati",
                            "Build frontend superata",
                            "Versione algoritmo registrata",
                            "Profili grading bloccati",
                            "Report validazione collegato",
                            "Manuale e SOP revisionati",
                        ),
                        "freeze",
                    ),
                ),
            ),
            Section(
                "Approvazione",
                (
                    Field("Note", "note", multiline=True, height=70),
                    Field("Approvazione responsabile tecnico", "approvazione_tecnica"),
                    Field("Approvazione responsabile qualita", "approvazione_qualita"),
                ),
            ),
        ),
    ),
)


class FormPdfBuilder:
    def __init__(self, canvas: Canvas, document_prefix: str) -> None:
        self.canvas = canvas
        self.form: AcroForm = canvas.acroForm
        self.document_prefix = document_prefix
        self.page = 0
        self.y = TOP_Y

    def new_page(self, title: str, code: str, subtitle: str) -> None:
        if self.page:
            self.canvas.showPage()
        self.page += 1
        self.y = TOP_Y
        self.canvas.setTitle("Solidita 4.0 - Moduli Accredia compilabili")
        self._header(title, code, subtitle)
        self._footer()

    def _header(self, title: str, code: str, subtitle: str) -> None:
        self.canvas.setFillColor(colors.HexColor("#0f172a"))
        self.canvas.rect(0, PAGE_HEIGHT - 86, PAGE_WIDTH, 86, stroke=0, fill=1)
        self.canvas.setFillColor(colors.white)
        self.canvas.setFont(FONT_BOLD, 15)
        self.canvas.drawString(MARGIN_X, PAGE_HEIGHT - 34, f"Solidita 4.0 - {code}")
        self.canvas.setFont(FONT_BOLD, 12)
        self.canvas.drawString(MARGIN_X, PAGE_HEIGHT - 54, title)
        self.canvas.setFont(FONT, 8.5)
        self.canvas.drawString(MARGIN_X, PAGE_HEIGHT - 72, subtitle[:110])
        self.y = PAGE_HEIGHT - 110

    def _footer(self) -> None:
        self.canvas.setFillColor(colors.HexColor("#64748b"))
        self.canvas.setFont(FONT, 7.5)
        self.canvas.drawString(
            MARGIN_X,
            24,
            "Template interno compilabile - non sostituisce i moduli ufficiali Accredia vigenti.",
        )
        self.canvas.drawRightString(PAGE_WIDTH - MARGIN_X, 24, f"Pagina {self.page}")

    def ensure_space(self, needed: float, form: FormDefinition) -> None:
        if self.y - needed < BOTTOM_Y:
            self.new_page(form.title, form.code, form.subtitle)

    def section_title(self, title: str, form: FormDefinition) -> None:
        self.ensure_space(30, form)
        self.canvas.setFillColor(colors.HexColor("#e2e8f0"))
        self.canvas.roundRect(MARGIN_X, self.y - 18, PAGE_WIDTH - (MARGIN_X * 2), 22, 4, fill=1)
        self.canvas.setFillColor(colors.HexColor("#0f172a"))
        self.canvas.setFont(FONT_BOLD, 10)
        self.canvas.drawString(MARGIN_X + 8, self.y - 12, title)
        self.y -= 30

    def text_field(self, field: Field, form: FormDefinition) -> None:
        row_height = field.height + ROW_GAP
        self.ensure_space(row_height, form)
        x_label = MARGIN_X
        x_field = MARGIN_X + LABEL_WIDTH
        width = PAGE_WIDTH - MARGIN_X - x_field

        self.canvas.setFillColor(colors.HexColor("#334155"))
        self.canvas.setFont(FONT, 8)
        self.canvas.drawString(x_label, self.y - 12, field.label)

        flags = "multiline" if field.multiline else ""
        self.form.textfield(
            name=self._field_name(form, field.name),
            x=x_field,
            y=self.y - field.height,
            width=width,
            height=field.height,
            borderStyle="inset",
            borderColor=colors.HexColor("#94a3b8"),
            fillColor=colors.HexColor("#ffffff"),
            textColor=colors.HexColor("#0f172a"),
            forceBorder=True,
            fontName=FONT,
            fontSize=8,
            value=field.value,
            fieldFlags=flags,
        )
        self.y -= row_height

    def table_field(self, table: TableField, form: FormDefinition) -> None:
        row_height = 22
        header_height = 20
        label_height = 16
        needed = label_height + header_height + (len(table.rows) * row_height) + SECTION_GAP
        self.ensure_space(needed, form)

        x = MARGIN_X
        width = PAGE_WIDTH - (MARGIN_X * 2)
        col_widths = self._column_widths(table.columns, width)

        self.canvas.setFillColor(colors.HexColor("#334155"))
        self.canvas.setFont(FONT_BOLD, 8)
        self.canvas.drawString(x, self.y - 10, table.label)
        self.y -= label_height

        self.canvas.setFillColor(colors.HexColor("#f1f5f9"))
        self.canvas.rect(x, self.y - header_height, width, header_height, fill=1, stroke=0)
        self.canvas.setFillColor(colors.HexColor("#0f172a"))
        self.canvas.setFont(FONT_BOLD, 7)
        current_x = x
        for index, column in enumerate(table.columns):
            self.canvas.drawString(current_x + 3, self.y - 13, column[:22])
            current_x += col_widths[index]
        self.y -= header_height

        for row_index, row_label in enumerate(table.rows):
            self.ensure_space(row_height + 8, form)
            current_x = x
            for col_index, column in enumerate(table.columns):
                cell_width = col_widths[col_index]
                if col_index == 0 and not table.first_column_editable:
                    self.canvas.setStrokeColor(colors.HexColor("#94a3b8"))
                    self.canvas.rect(current_x, self.y - row_height, cell_width, row_height)
                    self.canvas.setFillColor(colors.HexColor("#0f172a"))
                    self.canvas.setFont(FONT, 6.8)
                    self.canvas.drawString(current_x + 3, self.y - 14, row_label[:32])
                    current_x += cell_width
                    continue

                field_name = self._field_name(
                    form,
                    f"{table.name_prefix}_{row_index + 1}_{self._safe_name(column)}",
                )
                value = "" if table.first_column_editable else ""
                self.form.textfield(
                    name=field_name,
                    x=current_x,
                    y=self.y - row_height,
                    width=cell_width,
                    height=row_height,
                    borderStyle="inset",
                    borderColor=colors.HexColor("#cbd5e1"),
                    fillColor=colors.white,
                    textColor=colors.HexColor("#0f172a"),
                    forceBorder=True,
                    fontName=FONT,
                    fontSize=6.8,
                    value=value,
                )
                current_x += cell_width
            self.y -= row_height
        self.y -= SECTION_GAP

    def _column_widths(self, columns: tuple[str, ...], width: float) -> list[float]:
        if len(columns) == 2:
            return [width * 0.34, width * 0.66]
        if len(columns) == 3:
            return [width * 0.42, width * 0.24, width * 0.34]
        if len(columns) == 4:
            return [width * 0.35, width * 0.2, width * 0.2, width * 0.25]
        if len(columns) == 5:
            return [width * 0.16, width * 0.31, width * 0.22, width * 0.12, width * 0.19]
        if len(columns) == 7:
            return [
                width * 0.22,
                width * 0.08,
                width * 0.16,
                width * 0.12,
                width * 0.1,
                width * 0.15,
                width * 0.17,
            ]
        if len(columns) == 8:
            return [
                width * 0.08,
                width * 0.24,
                width * 0.11,
                width * 0.09,
                width * 0.09,
                width * 0.19,
                width * 0.13,
                width * 0.07,
            ]
        return [width / len(columns)] * len(columns)

    def _field_name(self, form: FormDefinition, name: str) -> str:
        return f"{self.document_prefix}.{form.code}.{name}"

    @staticmethod
    def _safe_name(value: str) -> str:
        return (
            value.lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("+", "plus")
            .replace("-", "_")
            .replace(".", "")
        )


def draw_form(canvas: Canvas, form: FormDefinition, document_prefix: str) -> None:
    builder = FormPdfBuilder(canvas, document_prefix)
    builder.new_page(form.title, form.code, form.subtitle)
    for section in form.sections:
        builder.section_title(section.title, form)
        for field in section.fields:
            if isinstance(field, Field):
                builder.text_field(field, form)
            else:
                builder.table_field(field, form)


def write_pdf(path: Path, forms: tuple[FormDefinition, ...], document_prefix: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(path), pagesize=A4)
    for index, form in enumerate(forms):
        if index:
            canvas.showPage()
        draw_form(canvas, form, document_prefix)
    canvas.save()
    enable_need_appearances(path)


def enable_need_appearances(path: Path) -> None:
    if PdfReader is None or PdfWriter is None:
        return

    reader = PdfReader(str(path))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    if "/AcroForm" in reader.trailer["/Root"]:
        source_acroform = reader.trailer["/Root"]["/AcroForm"]
        valid_fields = ArrayObject()
        for page in writer.pages:
            for annotation_ref in page.get("/Annots", []):
                annotation = annotation_ref.get_object()
                if (
                    annotation.get("/Subtype") == "/Widget"
                    and annotation.get("/T")
                    and annotation.get("/FT")
                ):
                    valid_fields.append(annotation_ref)
        acroform = DictionaryObject()
        if source_acroform.get("/DR"):
            acroform.update({NameObject("/DR"): source_acroform["/DR"]})
        if source_acroform.get("/DA"):
            acroform.update({NameObject("/DA"): source_acroform["/DA"]})
        acroform.update({NameObject("/Fields"): valid_fields})
        writer._root_object.update({NameObject("/AcroForm"): acroform})  # noqa: SLF001
        writer.set_need_appearances_writer(True)
        writer._root_object["/AcroForm"].update(  # noqa: SLF001
            {NameObject("/NeedAppearances"): BooleanObject(True)}
        )

    with path.open("wb") as file:
        writer.write(file)


def verify_fields(path: Path) -> int:
    if PdfReader is None:
        return -1
    reader = PdfReader(str(path))
    fields = reader.get_fields() or {}
    return len(fields)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for form in FORMS:
        filename = f"{form.code}_{form.title.lower().replace(' ', '_')}_compilabile.pdf"
        path = OUTPUT_DIR / filename
        write_pdf(path, (form,), form.code.lower())
        generated.append(path)

    bundle = OUTPUT_DIR / "Solidita_Accredia_Moduli_Compilabili.pdf"
    write_pdf(bundle, FORMS, "solidita_accredia")
    generated.append(bundle)

    for path in generated:
        field_count = verify_fields(path)
        suffix = "campi non verificati" if field_count < 0 else f"{field_count} campi"
        print(f"{path.relative_to(ROOT)} - {suffix}")


if __name__ == "__main__":
    main()
