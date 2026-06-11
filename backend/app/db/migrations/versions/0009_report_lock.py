"""report finalisation / lock (immutability after emission)

Revision ID: 0009_report_lock
Revises: 0008_calibration_references
Create Date: 2026-06-10

A report is already an immutable snapshot (frozen payload + SHA-256 seal). This
adds an explicit FINAL state: once locked, a report is the official emission and
the test job cannot silently emit another one over it (accreditation: report not
modifiable after emission).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0009_report_lock"
down_revision: str | None = "0008_calibration_references"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE quality_reports ADD COLUMN locked_at TIMESTAMPTZ;")


def downgrade() -> None:
    op.execute("ALTER TABLE quality_reports DROP COLUMN IF EXISTS locked_at;")
