"""refresh token store (rotation + reuse detection)

Revision ID: 0003_refresh_tokens
Revises: 0002_seed_test_methods
Create Date: 2026-06-09
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003_refresh_tokens"
down_revision: str | None = "0002_seed_test_methods"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE refresh_tokens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            jti UUID UNIQUE NOT NULL,
            family_id UUID NOT NULL,
            issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ NOT NULL,
            revoked BOOLEAN NOT NULL DEFAULT FALSE,
            used_at TIMESTAMPTZ,
            replaced_by_jti UUID
        );
        """
    )
    op.execute("CREATE INDEX ix_refresh_tokens_user ON refresh_tokens (user_id);")
    op.execute("CREATE INDEX ix_refresh_tokens_family ON refresh_tokens (family_id);")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solidita_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON refresh_tokens TO solidita_app;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS refresh_tokens;")
