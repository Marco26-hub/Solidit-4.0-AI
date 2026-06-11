"""Solidità 4.0 — FastAPI application entrypoint."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.accreditation.router import router as accreditation_router
from app.account.router import router as account_router
from app.articles.router import router as articles_router
from app.auth.router import router as auth_router
from app.batches.router import router as batches_router
from app.billing.router import router as billing_router
from app.brand_specs.router import router as brand_specs_router
from app.calibration.router import router as calibration_router
from app.captures.router import router as captures_router
from app.common.errors import register_exception_handlers
from app.common.logging import configure_logging
from app.companies.router import router as companies_router
from app.config import settings
from app.departments.router import router as departments_router
from app.devices.router import router as devices_router
from app.reports.public_router import router as public_reports_router
from app.reports.router import router as reports_router
from app.test_jobs.router import router as test_jobs_router
from app.test_methods.router import router as test_methods_router
from app.validation.router import router as validation_router

configure_logging()

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "Digital textile quality control, traceability, pre-validation and "
        "standardization platform (Trace core)."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(companies_router)
app.include_router(departments_router)
app.include_router(devices_router)
app.include_router(brand_specs_router)
app.include_router(batches_router)
app.include_router(test_methods_router)
app.include_router(test_jobs_router)
app.include_router(reports_router)
app.include_router(public_reports_router)
app.include_router(account_router)
app.include_router(billing_router)
app.include_router(captures_router)
app.include_router(articles_router)
app.include_router(calibration_router)
app.include_router(validation_router)
app.include_router(accreditation_router)


@app.get("/healthz", tags=["meta"])
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "version": __version__}


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs"}
