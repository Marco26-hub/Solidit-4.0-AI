# DATABASE_SCHEMA.md — Solidità 4.0

## Principi

- Multi-tenant rigoroso tramite `company_id`.
- Row Level Security su tutte le tabelle tenant-sensitive.
- UUID come primary key.
- JSONB per dati variabili: telemetria, risultati, configurazioni.
- Audit log append-only.
- Soft delete dove necessario.

## Tabelle principali

```
companies
users
company_memberships
roles
departments
devices
hardware_kits
reference_tiles
calibration_events
brand_specifications
brand_acceptance_rules
multifiber_batches
test_methods
test_jobs
capture_sessions
image_assets
measurement_results
quality_reports
report_signatures
audit_log
model_versions
validation_runs
subscriptions
api_keys
```

## DDL base

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

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
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE company_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    permissions JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(company_id, user_id)
);

CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(company_id, code)
);

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
    UNIQUE(company_id, hardware_uuid)
);

CREATE TABLE brand_specifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    brand_name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(company_id, brand_name)
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
    UNIQUE(company_id, batch_code)
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
    UNIQUE(company_id, report_number)
);

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
```

## Row Level Security esempio

```sql
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_specifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE multifiber_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE capture_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE image_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE measurement_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE quality_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_devices
ON devices
USING (company_id = current_setting('app.current_company_id')::uuid);

CREATE POLICY tenant_isolation_quality_reports
ON quality_reports
USING (company_id = current_setting('app.current_company_id')::uuid);
```

## Nota implementativa

Ogni request autenticata deve impostare:

```sql
SET app.current_company_id = '<uuid>';
```

Questo va fatto a livello middleware/sessione DB.
