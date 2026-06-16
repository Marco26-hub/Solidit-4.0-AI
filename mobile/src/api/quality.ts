// Read-only lookups the capture flow needs to build a real CaptureSession config.
import { apiFetch } from "./client";

export interface TestJob {
  id: string;
  article_code: string | null;
  lot_code: string | null;
  status: string;
  article_variant_id: string | null;
}
export interface Batch {
  id: string;
  batch_code: string;
  strip_profile_code: string | null;
}
export interface TestMethod {
  id: string;
  code: string;
  name: string;
  standard_family: string | null;
}
export interface CalibrationRef {
  id: string;
  kind: string;
  code: string;
  validity: string;
}

export const listTestJobs = () => apiFetch<TestJob[]>("/api/v1/test-jobs");
export const listBatches = () => apiFetch<Batch[]>("/api/v1/multifiber-batches");
export const listTestMethods = () => apiFetch<TestMethod[]>("/api/v1/test-methods");
export const listCalibrationRefs = () =>
  apiFetch<CalibrationRef[]>("/api/v1/calibration-references");
