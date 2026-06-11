"""public report-verification mirror (anyone can check a report's integrity)

Revision ID: 0013_report_verifications
Revises: 0012_aatcc_astm_methods
Create Date: 2026-06-11

A small mirror table with ONLY non-sensitive verification fields, readable
without authentication (RLS policy USING true), so a brand/customer scanning the
report QR can confirm authenticity (number, hash, company, issue date, locked
state) without exposing tenant data. The full report stays tenant-scoped.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0013_report_verifications"
down_revision: str | None = "0012_aatcc_astm_methods"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DDL = """
CREATE TABLE report_verifications (
    report_id UUID PRIMARY KEY REFERENCES quality_reports(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    report_number TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    company_name TEXT NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    locked BOOLEAN NOT NULL DEFAULT FALSE
);
"""


def upgrade() -> None:
    op.execute(DDL)
    op.execute("ALTER TABLE report_verifications ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE report_verifications FORCE ROW LEVEL SECURITY;")
    # public read (non-sensitive verification fields); writes only into own tenant
    op.execute(
        """
        CREATE POLICY public_read ON report_verifications
        FOR SELECT USING (true);
        """
    )
    op.execute(
        """
        CREATE POLICY tenant_write ON report_verifications
        FOR ALL
        USING (company_id = app_current_company_id())
        WITH CHECK (company_id = app_current_company_id());
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solidita_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON report_verifications TO solidita_app;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS report_verifications;")
