-- ─────────────────────────────────────────────────────────────
-- Solidità 4.0 — Postgres bootstrap (runs once on first cluster init).
--
-- Creates the runtime application role. CRITICAL for multi-tenant
-- isolation: this role is NON-superuser and NOBYPASSRLS, so Row
-- Level Security is actually enforced for it. Migrations run as the
-- superuser (postgres) and own the tables; the app connects as
-- solidita_app and is fully subject to RLS (+ FORCE RLS in migrations).
-- ─────────────────────────────────────────────────────────────

DO
$$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solidita_app') THEN
        CREATE ROLE solidita_app
            WITH LOGIN
                 PASSWORD 'solidita_app'
                 NOSUPERUSER
                 NOCREATEDB
                 NOCREATEROLE
                 NOBYPASSRLS;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE solidita TO solidita_app;
GRANT USAGE ON SCHEMA public TO solidita_app;

-- Tables/sequences are created later by the migration (superuser) role.
-- Default privileges ensure the app role gets DML on those future objects,
-- but NOT ownership (so it can never bypass RLS as owner).
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO solidita_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO solidita_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO solidita_app;
