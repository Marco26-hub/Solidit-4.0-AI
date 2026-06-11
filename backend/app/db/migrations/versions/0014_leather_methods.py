"""seed leather colour-fastness methods (ISO + IULTCS/IUF)

Revision ID: 0014_leather_methods
Revises: 0013_report_verifications
Create Date: 2026-06-11

CODES + public Italian titles only (a registry), NOT the copyrighted standard
text. Leather has its own colour-fastness standards (ISO 116xx / 157xx / 177xx
and the IULTCS IUF series), distinct from the textile ISO 105 family.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_leather_methods"
down_revision: str | None = "0013_report_verifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (code, title, category, family)
METHODS = [
    # ── ISO cuoio ────────────────────────────────────────────────────────────
    (
        "ISO_11640",
        "Solidità del colore allo sfregamento avanti/indietro — cuoio (ISO 11640)",
        "rubbing",
        "ISO cuoio",
    ),
    ("ISO_11641", "Solidità del colore al sudore — cuoio (ISO 11641)", "perspiration", "ISO cuoio"),
    ("ISO_11642", "Solidità del colore all'acqua — cuoio (ISO 11642)", "water", "ISO cuoio"),
    (
        "ISO_15700",
        "Solidità del colore alla goccia d'acqua — cuoio (ISO 15700)",
        "water_spotting",
        "ISO cuoio",
    ),
    (
        "ISO_17700",
        "Solidità/aderenza delle finiture allo sfregamento — cuoio (ISO 17700)",
        "rubbing",
        "ISO cuoio",
    ),
    # ── IULTCS / IUF ─────────────────────────────────────────────────────────
    ("IUF_421", "Solidità del colore allo sfregamento (IULTCS IUF 421)", "rubbing", "IULTCS"),
    ("IUF_426", "Solidità del colore al sudore (IULTCS IUF 426)", "perspiration", "IULTCS"),
    ("IUF_434", "Solidità del colore alla luce (IULTCS IUF 434)", "light", "IULTCS"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for code, name, category, family in METHODS:
        conn.execute(
            sa.text(
                "INSERT INTO test_methods (code, name, category, standard_family) "
                "VALUES (:code, :name, :category, :family) ON CONFLICT (code) DO NOTHING"
            ),
            {"code": code, "name": name, "category": category, "family": family},
        )


def downgrade() -> None:
    codes = ", ".join(f"'{m[0]}'" for m in METHODS)
    op.execute(f"DELETE FROM test_methods WHERE code IN ({codes});")
