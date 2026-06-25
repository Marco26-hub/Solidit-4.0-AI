"""Camera characterisation + measurement-uncertainty API.

The honest, accreditable colour path: fit a per-kit camera RGB→colour transform
from a ColorChecker (root-polynomial) so captured ΔE/grade is colorimeter-grade,
and quantify the measurement uncertainty (ISO 17025 §7.6). No spectral
reconstruction; scope is opaque samples under the capture illuminant.
"""
