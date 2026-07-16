"""operator authorizations registry + operator identity on results

Revision ID: 0016_operator_authorizations
Revises: 0015_proficiency_tests
Create Date: 2026-07-16

ISO/IEC 17025 clause 6.2 (personnel): the laboratory must authorise personnel for
specific activities/methods and keep records; every result must be traceable to
the operator who produced it. This adds:
- operator_authorizations: per-tenant registry (who is authorised to which test
  method, by whom, from/until when, with training notes). method_code NULL means
  "all methods" (general authorisation).
- measurement_results.operator_user_id: the identity of the operator who produced
  the result (capture_sessions already records operator_id at capture time).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0016_operator_authorizations"
down_revision: str | None = "0015_proficiency_tests"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DDL = """
CREATE TABLE operator_authorizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    method_code TEXT,                      -- NULL = authorised for all methods
    authorized_by UUID REFERENCES users(id) ON DELETE SET NULL,
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_until DATE,                      -- NULL = no expiry (until revoked)
    training_notes TEXT,                   -- training/qualification evidence ref
    status TEXT NOT NULL DEFAULT 'active', -- active | revoked
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_opauth_company ON operator_authorizations (company_id);
CREATE INDEX ix_opauth_user ON operator_authorizations (company_id, user_id);

ALTER TABLE measurement_results
    ADD COLUMN operator_user_id UUID REFERENCES users(id) ON DELETE SET NULL;
"""


def upgrade() -> None:
    op.execute(DDL)
    op.execute("ALTER TABLE operator_authorizations ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE operator_authorizations FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON operator_authorizations "
        "USING (company_id = app_current_company_id()) "
        "WITH CHECK (company_id = app_current_company_id());"
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solidita_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON operator_authorizations TO solidita_app;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE measurement_results DROP COLUMN IF EXISTS operator_user_id;")
    op.execute("DROP TABLE IF EXISTS operator_authorizations;")
