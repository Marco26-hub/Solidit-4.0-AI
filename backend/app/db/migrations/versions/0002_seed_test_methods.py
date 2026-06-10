"""seed global test_methods reference

Revision ID: 0002_seed_test_methods
Revises: 0001_initial
Create Date: 2026-06-09

Seeds common colour-fastness / dimensional method CODES only. NOTE: we store
codes + names as reference identifiers; we do NOT embed proprietary ISO/AATCC
equations or grey-scale tables here (those are configurable, licensed profiles).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0002_seed_test_methods"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

METHODS = [
    ("ISO_105_A02", "Grey scale for colour change", "reporting", "ISO 105-A"),
    ("ISO_105_A03", "Grey scale for staining", "reporting", "ISO 105-A"),
    ("ISO_105_C06", "Colour fastness to domestic/commercial laundering", "wash", "ISO 105-C"),
    ("ISO_105_E04", "Colour fastness to perspiration", "sweat", "ISO 105-E"),
    ("ISO_105_X12", "Colour fastness to rubbing (crocking)", "rubbing", "ISO 105-X"),
    ("AATCC_8", "Colorfastness to crocking (AATCC crockmeter)", "rubbing", "AATCC"),
    ("AATCC_61", "Colorfastness to laundering (accelerated)", "wash", "AATCC"),
    ("DIM_SHRINKAGE", "Dimensional change (shrinkage) after washing", "shrinkage", "internal"),
    ("PILLING", "Pilling / fuzzing assessment", "pilling", "internal"),
]


def upgrade() -> None:
    for code, name, category, family in METHODS:
        op.execute(
            "INSERT INTO test_methods (code, name, category, standard_family) "
            f"VALUES ('{code}', '{name.replace(chr(39), chr(39) * 2)}', '{category}', '{family}') "
            "ON CONFLICT (code) DO NOTHING;"
        )


def downgrade() -> None:
    codes = ", ".join(f"'{m[0]}'" for m in METHODS)
    op.execute(f"DELETE FROM test_methods WHERE code IN ({codes});")
