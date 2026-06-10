"""capture_sessions: add batch_id + test_method_code

Revision ID: 0005_capture_session_fields
Revises: 0004_strip_profiles
Create Date: 2026-06-09
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0005_capture_session_fields"
down_revision: str | None = "0004_strip_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE capture_sessions "
        "ADD COLUMN batch_id UUID REFERENCES multifiber_batches(id), "
        "ADD COLUMN test_method_code TEXT;"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE capture_sessions "
        "DROP COLUMN IF EXISTS batch_id, DROP COLUMN IF EXISTS test_method_code;"
    )
