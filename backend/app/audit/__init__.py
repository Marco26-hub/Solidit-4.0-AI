"""Audit query / export endpoints (Sprint 5+). The *writer* lives in
``app.common.audit`` and is already used across the Trace core. The
``audit_log`` table is append-only (UPDATE/DELETE revoked from the app role)."""
