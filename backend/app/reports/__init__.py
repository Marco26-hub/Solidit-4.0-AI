"""Quality report service: PDF generation, SHA-256 integrity seal, QR verify,
certificate ledger, signed-URL download. Implemented in Sprint 4 (Phase 3).
Tables ``quality_reports`` / ``report_signatures`` exist already.

NB (positioning): the SHA-256 value is a *cryptographic integrity seal*, NOT a
qualified digital signature. Reports are 'Digital Quality Reports'."""
