# Solidità 4.0 — Admin Portal (frontend)

React + TypeScript + Vite + Tailwind + TanStack Query. Skeleton (Sprint 0):
backend health check, login page wired to `/api/v1/auth/login`, typed API client.

```bash
cd frontend
cp .env.example .env        # set VITE_API_BASE (default http://localhost:8000)
npm install
npm run dev                 # http://localhost:5173
npm run build               # type-check + production build
```

Feature areas land in Sprint 5 (`src/features/`): dashboard, brand-spec manager,
batch-zero registry, certificate ledger, device manager.
