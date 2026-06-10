"""articles + variants (production sample reference) + multi-norm grading profiles

Revision ID: 0006_articles_grading
Revises: 0005_capture_session_fields
Create Date: 2026-06-10

The report compares the tested multifiber/fabric against the dyehouse/printer
production sample; an article can have MULTIPLE variants (colorways/lots), each
with its own reference Lab. Grading profiles map ΔE→grade per norm family
(UNI EN ISO / AATCC / ASTM) and assessment type (staining|change). Builtin
profiles seeded here use EXAMPLE thresholds — NOT official standard tables —
and must be replaced/validated per company (configurable engine rule).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_articles_grading"
down_revision: str | None = "0005_capture_session_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# EXAMPLE thresholds only (placeholders; validate/license per company).
_STAIN = (
    '[{"max_delta_e":0.4,"grade":5.0},{"max_delta_e":1.25,"grade":4.5},'
    '{"max_delta_e":2.1,"grade":4.0},{"max_delta_e":2.95,"grade":3.5},'
    '{"max_delta_e":4.1,"grade":3.0},{"max_delta_e":5.8,"grade":2.5},'
    '{"max_delta_e":8.2,"grade":2.0},{"max_delta_e":11.6,"grade":1.5}]'
)
_CHANGE = (
    '[{"max_delta_e":0.8,"grade":5.0},{"max_delta_e":1.7,"grade":4.5},'
    '{"max_delta_e":2.5,"grade":4.0},{"max_delta_e":3.4,"grade":3.5},'
    '{"max_delta_e":4.8,"grade":3.0},{"max_delta_e":6.8,"grade":2.5},'
    '{"max_delta_e":9.6,"grade":2.0},{"max_delta_e":13.6,"grade":1.5}]'
)

PROFILES = [
    (
        "ISO_105_STAINING_EXAMPLE",
        "ISO 105-A03 staining (EXAMPLE — validate)",
        "ISO_105",
        "staining",
        _STAIN,
    ),
    (
        "ISO_105_CHANGE_EXAMPLE",
        "ISO 105-A02 colour change (EXAMPLE — validate)",
        "ISO_105",
        "change",
        _CHANGE,
    ),
    (
        "AATCC_STAINING_EXAMPLE",
        "AATCC EP2 staining (EXAMPLE — validate)",
        "AATCC",
        "staining",
        _STAIN,
    ),
    (
        "AATCC_CHANGE_EXAMPLE",
        "AATCC EP1 colour change (EXAMPLE — validate)",
        "AATCC",
        "change",
        _CHANGE,
    ),
    (
        "ASTM_CHANGE_EXAMPLE",
        "ASTM D2244-based colour change (EXAMPLE — validate)",
        "ASTM",
        "change",
        _CHANGE,
    ),
    ("ASTM_STAINING_EXAMPLE", "ASTM staining (EXAMPLE — validate)", "ASTM", "staining", _STAIN),
]

DDL = """
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name TEXT,
    composition TEXT,
    brand_specification_id UUID REFERENCES brand_specifications(id),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_article_company_code UNIQUE (company_id, code)
);
CREATE INDEX ix_articles_company ON articles (company_id);

CREATE TABLE article_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    color_name TEXT,
    lot_code TEXT,
    reference_lab JSONB,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_variant_article_code UNIQUE (company_id, article_id, code)
);
CREATE INDEX ix_variants_company ON article_variants (company_id);
CREATE INDEX ix_variants_article ON article_variants (article_id);

CREATE TABLE grading_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    standard_family TEXT NOT NULL,
    assessment_type TEXT NOT NULL,
    thresholds JSONB NOT NULL,
    is_builtin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_grading_profiles_company ON grading_profiles (company_id);

ALTER TABLE test_jobs ADD COLUMN article_id UUID REFERENCES articles(id);
ALTER TABLE test_jobs ADD COLUMN article_variant_id UUID REFERENCES article_variants(id);
"""


def upgrade() -> None:
    op.execute(DDL)

    # standard tenant RLS for articles/variants
    for table in ("articles", "article_variants"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING (company_id = app_current_company_id()) "
            f"WITH CHECK (company_id = app_current_company_id());"
        )

    # grading_profiles: builtins (company_id NULL) readable by everyone;
    # writes only into the caller's tenant.
    op.execute("ALTER TABLE grading_profiles ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE grading_profiles FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON grading_profiles
        USING (company_id IS NULL OR company_id = app_current_company_id())
        WITH CHECK (company_id = app_current_company_id());
        """
    )

    # Use bound params so the JSON threshold literals (which contain ':') are NOT
    # mis-parsed by SQLAlchemy text() as bind parameters.
    conn = op.get_bind()
    for code, name, family, atype, thresholds in PROFILES:
        conn.execute(
            sa.text(
                "INSERT INTO grading_profiles "
                "(code, name, standard_family, assessment_type, thresholds, is_builtin) "
                "VALUES (:code, :name, :family, :atype, CAST(:thresholds AS jsonb), TRUE) "
                "ON CONFLICT (code) DO NOTHING"
            ),
            {
                "code": code,
                "name": name,
                "family": family,
                "atype": atype,
                "thresholds": thresholds,
            },
        )

    # ASTM colour-difference practice as a selectable method
    op.execute(
        "INSERT INTO test_methods (code, name, category, standard_family) VALUES "
        "('ASTM_D2244', 'Colour difference calculation (instrumental)', 'instrumental', 'ASTM') "
        "ON CONFLICT (code) DO NOTHING;"
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solidita_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE
                    ON articles, article_variants, grading_profiles TO solidita_app;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE test_jobs DROP COLUMN IF EXISTS article_variant_id;")
    op.execute("ALTER TABLE test_jobs DROP COLUMN IF EXISTS article_id;")
    op.execute("DROP TABLE IF EXISTS grading_profiles;")
    op.execute("DROP TABLE IF EXISTS article_variants;")
    op.execute("DROP TABLE IF EXISTS articles;")
