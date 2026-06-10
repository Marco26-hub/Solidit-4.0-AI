"""initial schema: tenancy, devices, quality domain, reports, audit + RLS

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-09

Creates the full Solidità 4.0 schema. Tenant tables get ``company_id`` and
PostgreSQL Row Level Security (ENABLE + FORCE). The runtime role ``solidita_app``
is NON-superuser, so policies are enforced. ``audit_log`` is append-only
(UPDATE/DELETE revoked from the app role).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Tenant tables that use the simple policy: company_id == app_current_company_id()
TENANT_TABLES = [
    "departments",
    "devices",
    "hardware_kits",
    "reference_tiles",
    "calibration_events",
    "brand_specifications",
    "brand_acceptance_rules",
    "multifiber_batches",
    "test_jobs",
    "capture_sessions",
    "image_assets",
    "measurement_results",
    "quality_reports",
    "report_signatures",
    "validation_runs",
    "subscriptions",
    "api_keys",
]

# Tables that carry an updated_at column maintained by a trigger.
UPDATED_AT_TABLES = [
    "companies",
    "users",
    "company_memberships",
    "departments",
    "devices",
    "hardware_kits",
    "reference_tiles",
    "brand_specifications",
    "subscriptions",
]

DDL = r"""
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- updated_at trigger function
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- RLS GUC accessors (STABLE, no SECURITY DEFINER -> no bypass).
-- NULLIF makes an unset/empty GUC become NULL so policies FAIL CLOSED.
CREATE OR REPLACE FUNCTION app_current_company_id() RETURNS uuid
    LANGUAGE sql STABLE AS
$$ SELECT NULLIF(current_setting('app.current_company_id', true), '')::uuid $$;

CREATE OR REPLACE FUNCTION app_current_user_id() RETURNS uuid
    LANGUAGE sql STABLE AS
$$ SELECT NULLIF(current_setting('app.current_user_id', true), '')::uuid $$;

-- ── Identity / tenancy ──────────────────────────────────────────────────────
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    vat_number TEXT,
    account_tier TEXT NOT NULL DEFAULT 'trace',
    active_departments JSONB NOT NULL DEFAULT '{}'::jsonb,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    permissions JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE company_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    permissions JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_membership_company_user UNIQUE (company_id, user_id)
);

CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_department_company_code UNIQUE (company_id, code)
);

-- ── Devices / hardware / calibration ────────────────────────────────────────
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    hardware_uuid TEXT NOT NULL,
    model TEXT,
    os_version TEXT,
    mdm_managed BOOLEAN NOT NULL DEFAULT FALSE,
    calibration_profile JSONB NOT NULL DEFAULT '{}'::jsonb,
    active_d65_matrix JSONB,
    active_tl84_matrix JSONB,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_device_company_hw UNIQUE (company_id, hardware_uuid)
);

CREATE TABLE hardware_kits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    kit_type TEXT NOT NULL,
    serial TEXT,
    status TEXT NOT NULL DEFAULT 'dispatched',
    include_iphone BOOLEAN NOT NULL DEFAULT FALSE,
    shipping_address JSONB NOT NULL DEFAULT '{}'::jsonb,
    dispatched_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE reference_tiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    tile_type TEXT,
    reference_values JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_reference_tile_company_code UNIQUE (company_id, code)
);

CREATE TABLE calibration_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
    illuminant TEXT NOT NULL,
    matrix JSONB NOT NULL,
    performed_by UUID REFERENCES users(id),
    performed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Quality domain ──────────────────────────────────────────────────────────
CREATE TABLE brand_specifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    brand_name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_brand_spec_company_name UNIQUE (company_id, brand_name)
);

CREATE TABLE brand_acceptance_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    brand_specification_id UUID NOT NULL REFERENCES brand_specifications(id) ON DELETE CASCADE,
    test_method_code TEXT NOT NULL,
    fiber_code TEXT,
    max_delta_e NUMERIC(8,4),
    min_gray_scale_grade NUMERIC(3,1),
    rule_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    severity TEXT NOT NULL DEFAULT 'blocking',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE multifiber_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    batch_code TEXT NOT NULL,
    supplier TEXT,
    opened_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    reference_lab_values JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_batch_company_code UNIQUE (company_id, batch_code)
);

CREATE TABLE test_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    standard_family TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE test_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(id),
    brand_specification_id UUID REFERENCES brand_specifications(id),
    test_method_id UUID REFERENCES test_methods(id),
    barcode TEXT,
    article_code TEXT,
    lot_code TEXT,
    status TEXT NOT NULL DEFAULT 'created',
    requested_by UUID REFERENCES users(id),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE capture_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    test_job_id UUID NOT NULL REFERENCES test_jobs(id) ON DELETE CASCADE,
    device_id UUID REFERENCES devices(id),
    operator_id UUID REFERENCES users(id),
    capture_type TEXT NOT NULL,
    illuminant TEXT,
    telemetry JSONB NOT NULL DEFAULT '{}'::jsonb,
    validation_status TEXT NOT NULL DEFAULT 'pending',
    validation_errors JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE image_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    capture_session_id UUID REFERENCES capture_sessions(id) ON DELETE CASCADE,
    asset_type TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE measurement_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    test_job_id UUID NOT NULL REFERENCES test_jobs(id) ON DELETE CASCADE,
    capture_session_id UUID REFERENCES capture_sessions(id),
    algorithm_version TEXT NOT NULL,
    results JSONB NOT NULL,
    pass_fail JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Reports / signatures ────────────────────────────────────────────────────
CREATE TABLE quality_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    test_job_id UUID NOT NULL REFERENCES test_jobs(id) ON DELETE CASCADE,
    report_number TEXT NOT NULL,
    pdf_storage_key TEXT,
    report_payload JSONB NOT NULL,
    sha256_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'generated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_report_company_number UNIQUE (company_id, report_number)
);

CREATE TABLE report_signatures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    quality_report_id UUID NOT NULL REFERENCES quality_reports(id) ON DELETE CASCADE,
    signer_user_id UUID REFERENCES users(id),
    signature_type TEXT NOT NULL DEFAULT 'integrity_seal',
    sha256_hash TEXT NOT NULL,
    signed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- ── ML governance (AI Lab, future) ──────────────────────────────────────────
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    framework TEXT,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    dataset_lineage JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_model_name_version UNIQUE (name, version)
);

CREATE TABLE validation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    model_version_id UUID REFERENCES model_versions(id),
    dataset_ref TEXT,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Billing / API keys ──────────────────────────────────────────────────────
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    plan TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'trialing',
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    current_period_end TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    scopes JSONB NOT NULL DEFAULT '[]'::jsonb,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Audit (append-only) ─────────────────────────────────────────────────────
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    actor_user_id UUID REFERENCES users(id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Indexes (FK + JSONB GIN) ────────────────────────────────────────────────
CREATE INDEX ix_memberships_company ON company_memberships (company_id);
CREATE INDEX ix_memberships_user ON company_memberships (user_id);
CREATE INDEX ix_departments_company ON departments (company_id);
CREATE INDEX ix_devices_company ON devices (company_id);
CREATE INDEX ix_hardware_kits_company ON hardware_kits (company_id);
CREATE INDEX ix_reference_tiles_company ON reference_tiles (company_id);
CREATE INDEX ix_calibration_events_company ON calibration_events (company_id);
CREATE INDEX ix_calibration_events_device ON calibration_events (device_id);
CREATE INDEX ix_brand_specs_company ON brand_specifications (company_id);
CREATE INDEX ix_brand_rules_company ON brand_acceptance_rules (company_id);
CREATE INDEX ix_brand_rules_spec ON brand_acceptance_rules (brand_specification_id);
CREATE INDEX ix_batches_company ON multifiber_batches (company_id);
CREATE INDEX ix_test_jobs_company ON test_jobs (company_id);
CREATE INDEX ix_test_jobs_status ON test_jobs (company_id, status);
CREATE INDEX ix_capture_sessions_company ON capture_sessions (company_id);
CREATE INDEX ix_capture_sessions_job ON capture_sessions (test_job_id);
CREATE INDEX ix_image_assets_company ON image_assets (company_id);
CREATE INDEX ix_image_assets_session ON image_assets (capture_session_id);
CREATE INDEX ix_measurements_company ON measurement_results (company_id);
CREATE INDEX ix_measurements_job ON measurement_results (test_job_id);
CREATE INDEX ix_reports_company ON quality_reports (company_id);
CREATE INDEX ix_report_signatures_company ON report_signatures (company_id);
CREATE INDEX ix_report_signatures_report ON report_signatures (quality_report_id);
CREATE INDEX ix_validation_runs_company ON validation_runs (company_id);
CREATE INDEX ix_subscriptions_company ON subscriptions (company_id);
CREATE INDEX ix_api_keys_company ON api_keys (company_id);
CREATE INDEX ix_audit_company ON audit_log (company_id);
CREATE INDEX ix_audit_created ON audit_log (created_at);

CREATE INDEX ix_capture_sessions_telemetry_gin ON capture_sessions USING GIN (telemetry);
CREATE INDEX ix_measurements_results_gin ON measurement_results USING GIN (results);
CREATE INDEX ix_reports_payload_gin ON quality_reports USING GIN (report_payload);
"""


def upgrade() -> None:
    op.execute(DDL)

    # updated_at triggers
    for table in UPDATED_AT_TABLES:
        op.execute(
            f"CREATE TRIGGER trg_{table}_updated_at BEFORE UPDATE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
        )

    # ── Row Level Security ──────────────────────────────────────────────────
    # Simple tenant tables.
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING (company_id = app_current_company_id()) "
            f"WITH CHECK (company_id = app_current_company_id());"
        )

    # companies: visible if it's the selected tenant OR the user is a member.
    op.execute("ALTER TABLE companies ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE companies FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON companies
        USING (
            id = app_current_company_id()
            OR id IN (
                SELECT company_id FROM company_memberships
                WHERE user_id = app_current_user_id()
            )
        )
        -- write-side: a row may only be created/mutated for the selected tenant.
        -- Registration pre-sets the company GUC before INSERT (see auth.service).
        WITH CHECK (id = app_current_company_id());
        """
    )

    # company_memberships: a user always sees their own rows; admins see their tenant's.
    op.execute("ALTER TABLE company_memberships ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE company_memberships FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON company_memberships
        -- READ: a user always sees their own memberships; admins see their tenant's.
        USING (
            company_id = app_current_company_id()
            OR user_id = app_current_user_id()
        )
        -- WRITE: a membership may ONLY be created/updated inside the currently
        -- selected tenant. The `user_id = ...` branch must NEVER be here, or a
        -- user could self-enroll into ANY company (cross-tenant takeover).
        WITH CHECK (company_id = app_current_company_id());
        """
    )

    # audit_log: tenant rows in tenant context; platform rows (null) only with no tenant.
    op.execute("ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;")
    # audit_log: strictly tenant-scoped. Platform (NULL company_id) audit rows are
    # privileged and are NOT written by the app role — the app always audits with a
    # company in context (login without a selected company is not audit-written here;
    # the authentication is audited at select-company instead).
    op.execute(
        """
        CREATE POLICY tenant_isolation ON audit_log
        USING (company_id = app_current_company_id())
        WITH CHECK (company_id = app_current_company_id());
        """
    )

    # ── Append-only audit: revoke UPDATE/DELETE from the app role ────────────
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solidita_app') THEN
                REVOKE UPDATE, DELETE ON audit_log FROM solidita_app;
                -- ensure DML grants exist even if default privileges were not set
                GRANT SELECT, INSERT, UPDATE, DELETE
                    ON ALL TABLES IN SCHEMA public TO solidita_app;
                REVOKE UPDATE, DELETE ON audit_log FROM solidita_app;
                GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO solidita_app;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP SCHEMA public CASCADE;")
    op.execute("CREATE SCHEMA public;")
