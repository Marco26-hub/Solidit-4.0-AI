# CLAUDE.md — Instructions for Claude Code

You are working on Solidità 4.0, a production-grade SaaS platform for textile quality control.

## Product positioning

Do not position the platform as an automatic replacement for an accredited laboratory.

Correct positioning:
> Digital textile quality control, traceability, pre-validation and standardization platform.

## Tech stack

Backend:
- Python 3.12+
- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL
- Pydantic v2
- Redis
- pytest

Vision:
- OpenCV
- scikit-image
- numpy
- scipy
- Pillow

Frontend:
- React
- TypeScript
- Tailwind CSS
- TanStack Query
- React Hook Form
- Zod

Mobile:
- React Native
- TypeScript
- iOS-first

Infrastructure:
- Docker Compose for local
- PostgreSQL
- Object storage compatible with S3
- CI/CD
- Environment-based configuration

## Non-negotiable architecture rules

1. Multi-tenant isolation is mandatory.
2. Every tenant-scoped table must include `company_id`.
3. PostgreSQL Row Level Security must be used.
4. Do not bypass tenant isolation in service code.
5. Do not hardcode ISO/AATCC proprietary equations if not provided/licensed.
6. Grey scale mapping must be configurable.
7. SHA-256 is an integrity hash, not a qualified digital signature.
8. Vision pipeline must separate geometry correction from color correction.
9. iPhone sensors are capture quality gates, not laboratory metrology by themselves.
10. Hardware kit/dima/lightbox is required for reliable Vision acquisition.

## Coding rules

- Write production-ready code.
- Add tests for every critical service.
- Use type hints.
- Keep modules small.
- Use dependency injection where appropriate.
- Do not store secrets in code.
- Use Pydantic models for request/response validation.
- Use Alembic migrations.
- Use structured logging.
- Include clear error messages.

## Backend structure proposal

```
backend/
  app/
    main.py
    config.py
    db/
      session.py
      models/
      migrations/
    auth/
    companies/
    devices/
    brand_specs/
    batches/
    test_jobs/
    captures/
    vision/
    reports/
    audit/
    common/
  tests/
```

## Vision structure proposal

```
backend/app/vision/
  capture_validation.py
  markers.py
  geometry.py
  color_correction.py
  lab.py
  delta_e.py
  grading.py
  pipeline.py
```

## Frontend structure proposal

```
frontend/
  src/
    app/
    components/
    features/
      dashboard/
      brand-specs/
      batch-zero/
      certificate-ledger/
      devices/
    lib/
    api/
```

## Mobile structure proposal

```
mobile/
  src/
    screens/
    components/
    camera/
    sensors/
    workflows/
    api/
    state/
```

## First task

Create the monorepo with:
- backend FastAPI skeleton;
- PostgreSQL docker-compose;
- Alembic;
- initial DDL/migrations;
- pytest setup;
- frontend skeleton;
- mobile skeleton placeholder;
- README with local setup.

Do not implement AI modules first. Start with Trace + Vision base.
