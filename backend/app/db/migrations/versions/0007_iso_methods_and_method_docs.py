"""seed UNI EN ISO 105 colour-fastness method catalog (colour change + multifibre
staining) + per-tenant uploadable reference-norm documents

Revision ID: 0007_iso_methods_and_method_docs
Revises: 0006_articles_grading
Create Date: 2026-06-10

We seed standard CODES + public titles only (a method registry) — NOT the
copyrighted standard text, procedures or grey-scale equations (those stay
configurable/licensed, see CLAUDE.md rule 5). The actual normative PDF is NOT
shipped: each company uploads ITS OWN licensed copy into `method_documents`
(tenant-scoped), so we never redistribute ISO/UNI/CEI copyrighted material.

ISO 105 colour-fastness methods that use the multifibre adjacent fabric assess
BOTH colour change of the specimen AND staining of each fibre of the multifibre.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_iso_methods_and_method_docs"
down_revision: str | None = "0006_articles_grading"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (code, public title, category, standard_family). standard_family keeps the
# human series label (e.g. "ISO 105-E"); the grading resolver normalises any
# "ISO 105-*" to the "ISO_105" grading-profile family. NOTE: ISO_105_E04
# (perspiration) is already seeded by migration 0002 — we only RENAME it to IT
# below, we do NOT re-insert it (so 0007 downgrade never deletes 0002's row).
METHODS = [
    # ── Water & aqueous liquids (E series — multifibre, colour change + staining)
    ("ISO_105_E01", "Solidità del colore all'acqua (ISO 105-E01)", "water", "ISO 105-E"),
    ("ISO_105_E02", "Solidità del colore all'acqua di mare (ISO 105-E02)", "seawater", "ISO 105-E"),
    (
        "ISO_105_E03",
        "Solidità del colore all'acqua clorata (acqua di piscina) (ISO 105-E03)",
        "chlorinated_water",
        "ISO 105-E",
    ),
    (
        "ISO_105_E05",
        "Solidità del colore alle macchie acide (ISO 105-E05)",
        "acid_spotting",
        "ISO 105-E",
    ),
    (
        "ISO_105_E06",
        "Solidità del colore alle macchie alcaline (ISO 105-E06)",
        "alkali_spotting",
        "ISO 105-E",
    ),
    (
        "ISO_105_E07",
        "Solidità del colore alle macchie d'acqua (ISO 105-E07)",
        "water_spotting",
        "ISO 105-E",
    ),
    ("ISO_105_E08", "Solidità del colore all'acqua calda (ISO 105-E08)", "hot_water", "ISO 105-E"),
    # ── Laundering / washing (C series — multifibre)
    (
        "ISO_105_C08",
        "Solidità del colore al lavaggio domestico (detergente non fosfatico) (ISO 105-C08)",
        "wash",
        "ISO 105-C",
    ),
    (
        "ISO_105_C10",
        "Solidità del colore al lavaggio con sapone o sapone e soda (ISO 105-C10)",
        "wash",
        "ISO 105-C",
    ),
    # ── Solvents / dry cleaning
    (
        "ISO_105_D01",
        "Solidità del colore al lavaggio a secco (percloroetilene) (ISO 105-D01)",
        "dry_clean",
        "ISO 105-D",
    ),
    # ── Light / weathering (colour change of specimen)
    (
        "ISO_105_B02",
        "Solidità del colore alla luce artificiale: lampada ad arco allo xeno (ISO 105-B02)",
        "light",
        "ISO 105-B",
    ),
    # ── Bleaching / heat
    (
        "ISO_105_N01",
        "Solidità del colore all'imbianchimento: ipoclorito (ISO 105-N01)",
        "bleach",
        "ISO 105-N",
    ),
    (
        "ISO_105_P01",
        "Solidità del colore al calore secco (escluso stiro) (ISO 105-P01)",
        "dry_heat",
        "ISO 105-P",
    ),
    (
        "ISO_105_X11",
        "Solidità del colore allo stiro a caldo (ISO 105-X11)",
        "hot_press",
        "ISO 105-X",
    ),
]

# E04 already exists (migration 0002, English title); localise it to IT here.
_E04_RENAME = "Solidità del colore al sudore (37 °C) (ISO 105-E04)"

DDL = """
CREATE TABLE method_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    test_method_code TEXT NOT NULL,
    filename TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    content_type TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_method_doc UNIQUE (company_id, test_method_code)
);
CREATE INDEX ix_method_documents_company ON method_documents (company_id);
"""


def upgrade() -> None:
    op.execute(DDL)

    op.execute("ALTER TABLE method_documents ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE method_documents FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON method_documents "
        "USING (company_id = app_current_company_id()) "
        "WITH CHECK (company_id = app_current_company_id());"
    )

    conn = op.get_bind()
    for code, name, category, family in METHODS:
        conn.execute(
            sa.text(
                "INSERT INTO test_methods (code, name, category, standard_family) "
                "VALUES (:code, :name, :category, :family) ON CONFLICT (code) DO NOTHING"
            ),
            {"code": code, "name": name, "category": category, "family": family},
        )

    # localise the pre-existing E04 (perspiration) title to Italian
    conn.execute(
        sa.text("UPDATE test_methods SET name = :name WHERE code = 'ISO_105_E04'"),
        {"name": _E04_RENAME},
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solidita_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON method_documents TO solidita_app;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS method_documents;")
    codes = ", ".join(f"'{m[0]}'" for m in METHODS)
    op.execute(f"DELETE FROM test_methods WHERE code IN ({codes});")
