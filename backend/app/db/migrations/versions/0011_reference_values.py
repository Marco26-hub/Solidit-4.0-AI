"""certified reference colour values on calibration references

Revision ID: 0011_reference_values
Revises: 0010_validation_samples
Create Date: 2026-06-11

A white tile / colour target carries CERTIFIED colour coordinates (CIELAB). When
present, the in-frame colour correction anchors the measured neutral patch to the
certified white instead of self-neutralising — metrologically stronger and
traceable to the reference's certificate.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0011_reference_values"
down_revision: str | None = "0010_validation_samples"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # {"L":.., "a":.., "b":..} for a white tile; future: list of patches for a target
    op.execute("ALTER TABLE calibration_references ADD COLUMN reference_values JSONB;")


def downgrade() -> None:
    op.execute("ALTER TABLE calibration_references DROP COLUMN IF EXISTS reference_values;")
