"""calibration references registry (grey scale / white tile / colour target /
lightbox) with validity + expiry, and per-capture instrument links

Revision ID: 0008_calibration_references
Revises: 0007_iso_methods_and_method_docs
Create Date: 2026-06-10

Accreditation foundation (ISO/IEC 17025 logic): physical references and the
lightbox must be identified, certified and IN DATE. A capture records which
instruments were used; analysis is BLOCKED when a linked reference is expired or
retired. We track validity here, not the copyrighted standard text.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0008_calibration_references"
down_revision: str | None = "0007_iso_methods_and_method_docs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DDL = """
CREATE TABLE calibration_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,                 -- grey_scale|white_tile|colour_target|lightbox|other
    code TEXT NOT NULL,
    description TEXT,
    certificate_number TEXT,
    valid_from DATE,
    valid_until DATE,
    status TEXT NOT NULL DEFAULT 'active',  -- active | retired
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_calref_company_kind_code UNIQUE (company_id, kind, code)
);
CREATE INDEX ix_calref_company ON calibration_references (company_id);

ALTER TABLE capture_sessions
    ADD COLUMN lightbox_ref_id UUID REFERENCES calibration_references(id),
    ADD COLUMN grey_scale_ref_id UUID REFERENCES calibration_references(id),
    ADD COLUMN white_tile_ref_id UUID REFERENCES calibration_references(id),
    ADD COLUMN colour_target_ref_id UUID REFERENCES calibration_references(id);
"""


def upgrade() -> None:
    op.execute(DDL)
    op.execute("ALTER TABLE calibration_references ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE calibration_references FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON calibration_references "
        "USING (company_id = app_current_company_id()) "
        "WITH CHECK (company_id = app_current_company_id());"
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solidita_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON calibration_references TO solidita_app;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE capture_sessions DROP COLUMN IF EXISTS colour_target_ref_id;")
    op.execute("ALTER TABLE capture_sessions DROP COLUMN IF EXISTS white_tile_ref_id;")
    op.execute("ALTER TABLE capture_sessions DROP COLUMN IF EXISTS grey_scale_ref_id;")
    op.execute("ALTER TABLE capture_sessions DROP COLUMN IF EXISTS lightbox_ref_id;")
    op.execute("DROP TABLE IF EXISTS calibration_references;")
