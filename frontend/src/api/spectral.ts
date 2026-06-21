// Spectral reflectance ESTIMATION (R&D) API.
//
// HONESTY CONTRACT (project rule 7): the reflectance curve is ESTIMATED from
// RGB/Lab — it is NOT a spectrophotometer measurement. RGB→spectrum is
// under-determined (metamerism), so results are indicative only and are
// excluded from the sealed report. The backend echoes this in `disclaimer`.

import { apiFetch } from "./client";

export type Illuminant = "D65" | "A";
export const ILLUMINANTS: Illuminant[] = ["D65", "A"];

/** CIELAB triple as the API expects it for the manual estimate. */
export interface LabInput {
  L: number;
  a: number;
  b: number;
}

/** Result of POST /spectral/estimate — an ESTIMATE, never a measurement. */
export interface ReflectanceEstimate {
  estimate: boolean;
  not_a_measurement: boolean;
  label: string;
  method: string;
  engine: string;
  illuminant: string;
  observer: string;
  wavelengths_nm: number[]; // length 31 (400..700 nm)
  reflectance: number[]; // length 31, each 0..1
  input_lab: number[]; // [L, a, b]
  roundtrip_lab: number[]; // [L, a, b]
  roundtrip_delta_e: number;
  confidence: number; // 0..1
  warnings: string[];
  disclaimer: string;
}

/** Result of POST /spectral/render-under — a predicted (ESTIMATED) appearance. */
export interface RenderUnderResult {
  estimate: boolean;
  illuminant: string;
  observer: string;
  lab: number[]; // [L, a, b]
  srgb: number[]; // [r, g, b] each 0..255
  disclaimer: string;
}

/** Per-illuminant colour difference inside a metamerism comparison. */
export interface IlluminantDiff {
  illuminant: string;
  delta_e: number;
  metamerism_index: number;
  lab_reference: number[];
  lab_sample: number[];
}

/** Result of POST /spectral/metamerism — ESTIMATED, indicative only. */
export interface MetamerismResult {
  estimate: boolean;
  not_a_measurement: boolean;
  label: string;
  method: string;
  reference_illuminant: string;
  observer: string;
  delta_e_reference: number;
  per_illuminant: IlluminantDiff[];
  warnings: string[];
  disclaimer: string;
}

/** One fiber's estimate inside a measurement-result expansion. */
export interface FiberEstimate {
  fiber: string;
  sample_lab: number[]; // [L, a, b]
  estimate: ReflectanceEstimate;
}

/** Result of GET /spectral/measurement-results/{id}. */
export interface MeasurementResultEstimate {
  measurement_result_id: string;
  label: string;
  disclaimer: string;
  note: string;
  fibers: FiberEstimate[];
}

// ── API functions ─────────────────────────────────────────────────────────────

export const estimateReflectance = (body: {
  lab: LabInput;
  illuminant?: Illuminant;
  observer?: string;
}) =>
  apiFetch<ReflectanceEstimate>("/api/v1/spectral/estimate", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const renderUnder = (body: {
  reflectance: number[];
  illuminant: Illuminant;
  observer?: string;
}) =>
  apiFetch<RenderUnderResult>("/api/v1/spectral/render-under", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const metamerism = (body: {
  lab_reference: LabInput;
  lab_sample: LabInput;
  reference_illuminant?: Illuminant;
  observer?: string;
}) =>
  apiFetch<MetamerismResult>("/api/v1/spectral/metamerism", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const estimateForResult = (resultId: string, illuminant: Illuminant = "D65") =>
  apiFetch<MeasurementResultEstimate>(
    `/api/v1/spectral/measurement-results/${resultId}?illuminant=${encodeURIComponent(illuminant)}`
  );
