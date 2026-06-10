# Solidità 4.0 — Backend

FastAPI + SQLAlchemy 2 (async) + PostgreSQL (Row Level Security) + Alembic.

This is the **Trace** core (Sprint 0+1): auth, companies, memberships, departments,
devices, multi-tenant isolation, audit log. Vision / reports / quality domain are
scaffolded as skeleton modules (see `app/vision`, `app/ai_lab`, etc.).

## Quick start (Docker — recommended)

```bash
cp .env.example .env                      # from repo root
docker compose -f infra/docker-compose.yml up -d
# backend runs migrations on boot, then serves on http://localhost:8000
open http://localhost:8000/docs
```

## Quick start (local, no Docker for the app)

Needs a reachable PostgreSQL 16 and the `solidita_app` role (see
`infra/postgres/init.sql`).

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head          # uses MIGRATION_DATABASE_URL
uvicorn app.main:app --reload
pytest -q
```

## Multi-tenant model (read before touching the DB)

- Every tenant table has `company_id` and PostgreSQL **RLS + FORCE RLS**.
- The app connects as **`solidita_app`** (NON-superuser, NOBYPASSRLS) so RLS is
  always enforced. Migrations run as a privileged role and own the tables.
- Per request, the DB session sets two transaction-local GUCs:
  - `app.current_user_id`  — always (the authenticated user)
  - `app.current_company_id` — when a tenant is selected (from the JWT)
  using `set_config(key, value, is_local => true)` inside the request transaction.
- Policies use `NULLIF(current_setting(key, true), '')::uuid` so an unset tenant
  yields NULL → **fails closed** (no rows, inserts rejected).

See `app/common/rls.py`, `app/db/session.py`, and the RLS block in
`app/db/migrations/versions/0001_initial.py`.
