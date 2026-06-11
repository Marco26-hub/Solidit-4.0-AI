"""method validation campaign: per-sample software-vs-reference rows

Revision ID: 0010_validation_samples
Revises: 0009_report_lock
Create Date: 2026-06-10

Accreditation keystone (the credibility document): a validation run holds N
samples, each with the software grade and the reference grade (spectrophotometer,
expert visual, or external lab). Statistics (mean grade deviation, % within ±0.5
grade, bias, max deviation) are computed into validation_runs.metrics. The
validation_runs table already exists (migration 0001); we add the sample rows.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0010_validation_samples"
down_revision: str | None = "0009_report_lock"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DDL = """
CREATE TABLE validation_samples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    validation_run_id UUID NOT NULL REFERENCES validation_runs(id) ON DELETE CASCADE,
    sample_code TEXT NOT NULL,
    fiber TEXT,
    reference_method TEXT NOT NULL DEFAULT 'spectrophotometer',
    software_grade NUMERIC(3,1),
    reference_grade NUMERIC(3,1),
    software_delta_e NUMERIC(8,3),
    reference_delta_e NUMERIC(8,3),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_validation_samples_company ON validation_samples (company_id);
CREATE INDEX ix_validation_samples_run ON validation_samples (validation_run_id);
"""


def upgrade() -> None:
    op.execute(DDL)
    op.execute("ALTER TABLE validation_samples ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE validation_samples FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON validation_samples "
        "USING (company_id = app_current_company_id()) "
        "WITH CHECK (company_id = app_current_company_id());"
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solidita_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON validation_samples TO solidita_app;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS validation_samples;")
