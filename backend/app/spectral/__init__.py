"""Spectral reflectance ESTIMATION (R&D) — STIMATA, never a measurement.

This package exposes an estimated reflectance curve derived from a measured
CIELAB colour. It is deliberately SEPARATE from the accredited measurement path
(Lab/ΔE/grade) and never written into the sealed Digital Quality Report
(project rule 7). The estimation engine lives in ``app.vision.spectral``; this
package adds the pluggable backend selection, request/response schemas and the
HTTP API.
"""
