#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Solidità 4.0 — Neon bootstrap.
#
# Usage:
#   NEON_OWNER_URL='postgres://neondb_owner:PWD@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require' \
#     ./infra/neon/setup_neon.sh
#
# What it does (idempotent):
#   1. creates the NON-superuser app role `solidita_app` (NOBYPASSRLS) with a
#      freshly generated password — RLS is only real if the app is not the owner
#   2. grants CONNECT/USAGE + default privileges (DML only, never ownership)
#   3. runs Alembic migrations AS THE OWNER (tables stay owned by neondb_owner,
#      so FORCE RLS applies to solidita_app)
#   4. prints the DATABASE_URL the backend must use (the app role, not owner)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

if [[ -z "${NEON_OWNER_URL:-}" ]]; then
  echo "ERROR: set NEON_OWNER_URL to the Neon owner connection string" >&2
  echo "  (Neon console → Connection Details → role neondb_owner, psql format)" >&2
  exit 1
fi

command -v psql >/dev/null || { echo "ERROR: psql not found" >&2; exit 1; }

DBNAME="$(psql "$NEON_OWNER_URL" -At -c 'SELECT current_database();')"
HOSTPART="$(printf '%s' "$NEON_OWNER_URL" | sed -E 's#^[^@]+@##')"

APP_PASSWORD="${SOLIDITA_APP_PASSWORD:-$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32)}"

echo "→ creating app role solidita_app on database ${DBNAME}"
psql "$NEON_OWNER_URL" -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solidita_app') THEN
        CREATE ROLE solidita_app
            WITH LOGIN PASSWORD '${APP_PASSWORD}'
                 NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
    ELSE
        ALTER ROLE solidita_app WITH LOGIN PASSWORD '${APP_PASSWORD}' NOBYPASSRLS;
    END IF;
END
\$\$;

GRANT CONNECT ON DATABASE ${DBNAME} TO solidita_app;
GRANT USAGE ON SCHEMA public TO solidita_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO solidita_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO solidita_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO solidita_app;
SQL

echo "→ running Alembic migrations as owner"
OWNER_SQLA_URL="$(printf '%s' "$NEON_OWNER_URL" | sed -E 's#^postgres(ql)?://#postgresql+asyncpg://#')"
PYTHON_BIN="${PYTHON_BIN:-python3}"
(
  cd "$(dirname "$0")/../../backend"
  DATABASE_URL="$OWNER_SQLA_URL" \
    MIGRATION_DATABASE_URL="$OWNER_SQLA_URL" \
    "$PYTHON_BIN" -m alembic upgrade head
)

echo "→ verifying RLS enforcement for solidita_app"
psql "$NEON_OWNER_URL" -At -c "
  SELECT count(*) FROM pg_tables t
  JOIN pg_class c ON c.relname = t.tablename
  WHERE t.schemaname='public' AND c.relrowsecurity AND c.relforcerowsecurity;" \
  | xargs -I{} echo "   tables with FORCE RLS: {}"

cat <<EOF

✅ Neon ready.

Backend env (the APP role — never the owner):
  DATABASE_URL=postgresql+asyncpg://solidita_app:${APP_PASSWORD}@${HOSTPART}

Keep the owner URL only for migrations:
  MIGRATION_DATABASE_URL=${OWNER_SQLA_URL}
EOF
