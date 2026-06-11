"""seed AATCC + ASTM colour-fastness methods (corresponding to the ISO 105 set)

Revision ID: 0012_aatcc_astm_methods
Revises: 0011_reference_values
Create Date: 2026-06-11

CODES + public Italian titles only (a registry), NOT the copyrighted standard
text. Each AATCC method records its closest ISO 105 equivalent in metadata so the
catalog shows the correspondence. ASTM colour-fastness is largely covered via
AATCC in the US; ASTM here is the instrumental colour-difference / indices set.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_aatcc_astm_methods"
down_revision: str | None = "0011_reference_values"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (code, title, category, family, iso_equivalent)
METHODS = [
    # ── AATCC (corrispondenze ISO 105) ───────────────────────────────────────
    (
        "AATCC_15",
        "Solidità del colore al sudore (AATCC 15)",
        "perspiration",
        "AATCC",
        "ISO_105_E04",
    ),
    ("AATCC_107", "Solidità del colore all'acqua (AATCC 107)", "water", "AATCC", "ISO_105_E01"),
    (
        "AATCC_162",
        "Solidità del colore all'acqua clorata di piscina (AATCC 162)",
        "chlorinated_water",
        "AATCC",
        "ISO_105_E03",
    ),
    ("AATCC_16", "Solidità del colore alla luce (AATCC 16)", "light", "AATCC", "ISO_105_B02"),
    (
        "AATCC_132",
        "Solidità del colore al lavaggio a secco (AATCC 132)",
        "dry_clean",
        "AATCC",
        "ISO_105_D01",
    ),
    (
        "AATCC_133",
        "Solidità del colore al calore/stiro (AATCC 133)",
        "hot_press",
        "AATCC",
        "ISO_105_X11",
    ),
    (
        "AATCC_188",
        "Solidità del colore all'ipoclorito di sodio (AATCC 188)",
        "bleach",
        "AATCC",
        "ISO_105_N01",
    ),
    (
        "AATCC_EP1",
        "Scala grigia per variazione colore (AATCC EP1)",
        "reporting",
        "AATCC",
        "ISO_105_A02",
    ),
    ("AATCC_EP2", "Scala grigia per staining (AATCC EP2)", "reporting", "AATCC", "ISO_105_A03"),
    # ── ASTM (strumentale: differenza colore / indici) ───────────────────────
    ("ASTM_E313", "Indici di bianco e giallo (ASTM E313)", "instrumental", "ASTM", None),
]


def upgrade() -> None:
    conn = op.get_bind()
    for code, name, category, family, iso_eq in METHODS:
        meta = json.dumps({"iso_equivalent": iso_eq} if iso_eq else {})
        conn.execute(
            sa.text(
                "INSERT INTO test_methods (code, name, category, standard_family, metadata) "
                "VALUES (:code, :name, :category, :family, CAST(:meta AS jsonb)) "
                "ON CONFLICT (code) DO NOTHING"
            ),
            {"code": code, "name": name, "category": category, "family": family, "meta": meta},
        )


def downgrade() -> None:
    codes = ", ".join(f"'{m[0]}'" for m in METHODS)
    op.execute(f"DELETE FROM test_methods WHERE code IN ({codes});")
