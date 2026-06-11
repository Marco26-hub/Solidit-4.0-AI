# Deploy — Solidità 4.0

## TL;DR

- **Frontend (Vite SPA)** → deploys cleanly on **Vercel**.
- **Backend (FastAPI + PostgreSQL + RLS + object storage)** → **does NOT run on Vercel**.
  It needs a long-running server, a real PostgreSQL with Row-Level Security, and
  persistent S3-compatible object storage. Host it on **Railway / Render / Fly.io**
  (managed Postgres) or a **VPS with the included Docker Compose**.

Vercel's "Services" multi-service import is shown in the new-project screen, but the
backend would break there (no persistent filesystem for image uploads, serverless
cold-starts vs the asyncpg pool, Alembic migrations, RLS role setup). Deploy the two
tiers separately.

---

## 1. Frontend on Vercel

In the Vercel import screen:

1. **Don't** use the "Services" preset. Click **Edit** on *Root Directory* and set it to **`frontend`**.
2. Framework preset: **Vite** (auto-detected). Build `npm run build`, output `dist`
   (already pinned by `frontend/vercel.json`, which also adds the SPA fallback rewrite).
3. **Environment Variables** → add:
   - `VITE_API_BASE = https://<your-backend-url>` (the public URL of the backend you deploy in step 2).
4. Deploy.

> The SPA rewrite in `frontend/vercel.json` makes deep links (`/articles`, `/methods`, …)
> serve `index.html` instead of 404.

---

## 2. Backend (Railway / Render / Fly.io / VPS)

Requirements the host must provide:

- **PostgreSQL 16** reachable over the network.
- A **non-superuser** app role `solidita_app` (RLS is bypassed by superusers — see `infra/postgres/init.sql`).
- **S3-compatible object storage** in production (the dev `LocalStorage` writes to the
  local filesystem and is NOT suitable for serverless/multi-instance).
- Python 3.12 with the `[vision]` optional deps installed (numpy/scikit-image/Pillow)
  if the photo-analysis endpoints are used.

### Steps

```bash
# 1. provision Postgres + create the non-superuser app role
psql "$ADMIN_DATABASE_URL" -f infra/postgres/init.sql

# 2. run migrations (sync psycopg2 driver, as configured in alembic env)
cd backend
pip install -e ".[vision]"
export DATABASE_URL="postgresql+asyncpg://solidita_app:...@host:5432/solidita"
python -m alembic upgrade head

# 3. run the API
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Required environment variables (backend)

| var | example | note |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://solidita_app:pwd@host:5432/solidita` | non-superuser role |
| `JWT_SECRET` | (random 32+ bytes) | never commit |
| `CORS_ORIGINS` | `https://<frontend>.vercel.app` | comma-separated |
| `PUBLIC_BASE_URL` | `https://api.example.com` | report verify links |
| `ENVIRONMENT` | `production` | enables HSTS header |
| storage (prod) | S3 endpoint/bucket/keys | replace `LocalStorage` (Phase 9) |

### Docker (VPS)

`infra/docker-compose.yml` already brings up Postgres 16 + Redis + backend for local/VPS use.
For production add TLS (reverse proxy), backups, and swap LocalStorage for S3.

---

## 3. After deploy

- Point the frontend's `VITE_API_BASE` at the backend URL and redeploy the frontend.
- Set the backend `CORS_ORIGINS` to the Vercel domain.
- Verify: register a company, log in, create an article → the full flow should work end-to-end.

> Positioning reminder (CLAUDE.md): this is a **digital imaging system for assisted
> pre-evaluation** of colour fastness, not a spectrophotometer replacement. Keep the
> disclaimer in reports.
