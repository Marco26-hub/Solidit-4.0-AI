"""inter-laboratory comparison / proficiency testing (PT) records + evaluation

Revision ID: 0015_proficiency_tests
Revises: 0014_leather_methods
Create Date: 2026-06-11

ISO/IEC 17025 clause 7.7.2 requires assuring validity of results, including
participation in proficiency testing / inter-laboratory comparisons. The external
PT scheme is run by an accredited provider; here we RECORD and EVALUATE the lab's
performance per round: z-score (vs assigned value + SDPA) and En number (bilateral
ILC with uncertainties), with a satisfactory/questionable/unsatisfactory verdict.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0015_proficiency_tests"
down_revision: str | None = "0014_leather_methods"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DDL = """
CREATE TABLE proficiency_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    scheme TEXT NOT NULL,                 -- PT provider / scheme name
    round_label TEXT NOT NULL,            -- round/cycle identifier
    parameter TEXT,                       -- parameter/material/method tested
    test_method_code TEXT,                -- optional link to a method
    result_x NUMERIC(10,4) NOT NULL,      -- the lab's reported value
    assigned_value NUMERIC(10,4) NOT NULL,-- assigned/reference value X
    std_dev NUMERIC(10,4),                -- sigma for proficiency assessment (SDPA)
    u_lab NUMERIC(10,4),                  -- lab expanded uncertainty (for En)
    u_ref NUMERIC(10,4),                  -- reference expanded uncertainty (for En)
    z_score NUMERIC(10,3),
    en_number NUMERIC(10,3),
    verdict TEXT NOT NULL DEFAULT 'n/d',
    test_date DATE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_proficiency_company ON proficiency_tests (company_id);
"""


def upgrade() -> None:
    op.execute(DDL)
    op.execute("ALTER TABLE proficiency_tests ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE proficiency_tests FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON proficiency_tests "
        "USING (company_id = app_current_company_id()) "
        "WITH CHECK (company_id = app_current_company_id());"
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solidita_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON proficiency_tests TO solidita_app;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS proficiency_tests;")
