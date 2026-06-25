// Camera colour CHARACTERISATION + measurement UNCERTAINTY API.
//
// HONESTY CONTRACT (in line with project rules): this is colorimeter-grade
// colour via camera characterisation. It is NOT a spectrophotometer and NOT
// spectral reconstruction. After characterisation the camera matches a
// colorimeter for OPAQUE samples, under the CAPTURE illuminant, within a
// validated ΔE. It does NOT cover multi-illuminant metamerism, UV / optical
// brighteners, nor gloss / effect colours. Input RGB must be LINEAR camera RGB
// (RAW / ProRAW-linearised) — NOT gamma-encoded sRGB.

import { apiFetch } from "./client";

export type PolynomialDegree = 1 | 2 | 3;
export const DEGREES: PolynomialDegree[] = [1, 2, 3];

/** Residual ΔE budget of a fit (CIEDE2000 against the reference Lab set). */
export interface ResidualBudget {
  mean_delta_e: number;
  max_delta_e: number;
  rms_delta_e: number;
  p95_delta_e: number;
}

/** Per-patch residual ΔE after applying the fitted transform. */
export interface PerPatchResidual {
  patch: number;
  delta_e: number;
}

/** Result of POST /colorimetry/characterize — the fitted RGB→XYZ transform. */
export interface CharacterizationResult {
  method: string;
  degree: number;
  n_terms: number;
  n_patches: number;
  reference: string;
  matrix: number[][];
  residual: ResidualBudget;
  per_patch: PerPatchResidual[];
}

/** Result of POST /colorimetry/apply — a single colour through the transform. */
export interface ApplyResult {
  xyz: [number, number, number] | number[];
  lab: [number, number, number] | number[];
}

/** One contribution to the combined uncertainty budget. */
export interface UncertaintyComponent {
  component: string;
  standard_uncertainty: number;
  distribution?: string | null;
  source?: string | null;
  degrees_freedom?: number | null;
  variance_share_pct: number;
}

/** Result of POST /colorimetry/uncertainty — ISO 17025 (simplified) budget. */
export interface UncertaintyResult {
  unit: string;
  components: UncertaintyComponent[];
  combined_standard_uncertainty: number;
  effective_degrees_freedom: number | null;
  coverage_factor: number;
  coverage_method: string;
  expanded_uncertainty: number;
  confidence_level: string | null;
  decision_rule: {
    rule: string;
    direction: string;
    measured_value: number;
    tolerance_limit: number;
    guard_band: number;
    verdict: string;
  } | null;
  dominant_component: string | null;
  note: string;
}

// ── request bodies ─────────────────────────────────────────────────────────────

export interface CharacterizeBody {
  /** Each row is [r, g, b] LINEAR camera RGB, 6..140 rows, values 0..1 or 0..255. */
  patches: number[][];
  degree: PolynomialDegree;
  /** Optional reference Lab set; when omitted the backend uses its default. */
  reference_lab?: number[][];
}

export interface ApplyBody {
  matrix: number[][];
  rgb: [number, number, number];
  degree: PolynomialDegree;
}

export interface UncertaintyBody {
  repeatability?: number;
  characterisation?: number;
  reproducibility?: number;
  reference?: number;
  components?: Array<{
    component: string;
    value?: number;
    input_type?: "standard_uncertainty" | "expanded_uncertainty" | "half_width" | "standard_deviation";
    distribution?: "normal" | "rectangular" | "triangular" | "u_shaped";
    coverage_factor?: number;
    degrees_freedom?: number;
    n?: number;
    use_mean?: boolean;
    observations?: number[];
  }>;
  coverage_factor?: number | null;
  confidence_level?: number;
  measured_value?: number;
  tolerance_limit?: number;
  decision_direction?: "max" | "min";
}

// ── API functions ─────────────────────────────────────────────────────────────

export const characterizeCamera = (body: CharacterizeBody) =>
  apiFetch<CharacterizationResult>("/api/v1/colorimetry/characterize", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const applyTransform = (body: ApplyBody) =>
  apiFetch<ApplyResult>("/api/v1/colorimetry/apply", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const computeUncertainty = (body: UncertaintyBody) =>
  apiFetch<UncertaintyResult>("/api/v1/colorimetry/uncertainty", {
    method: "POST",
    body: JSON.stringify(body),
  });
