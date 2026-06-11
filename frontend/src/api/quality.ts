import { apiFetch, getAccessToken } from "./client";
import type {
  AcceptanceRuleInput,
  Article,
  ArticleVariant,
  Batch,
  BrandSpec,
  CalibrationReference,
  GradingProfile,
  LabValue,
  MeasurementResult,
  Report,
  ReportVerify,
  StripProfile,
  TestJob,
  TestMethod,
} from "./types";

// ── Brand specs ───────────────────────────────────────────────────────────────
export const listBrandSpecs = () => apiFetch<BrandSpec[]>("/api/v1/brand-specifications");

export const createBrandSpec = (body: {
  brand_name: string;
  description?: string | null;
  rules: AcceptanceRuleInput[];
}) =>
  apiFetch<BrandSpec>("/api/v1/brand-specifications", {
    method: "POST",
    body: JSON.stringify(body),
  });

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function uploadCapitolato(specId: string, file: File): Promise<BrandSpec> {
  const token = getAccessToken();
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${API_BASE}/api/v1/brand-specifications/${specId}/document`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: fd,
  });
  if (!res.ok) throw new Error(`Upload fallito (${res.status})`);
  return res.json();
}

export async function downloadCapitolato(specId: string): Promise<Blob> {
  const token = getAccessToken();
  const res = await fetch(`${API_BASE}/api/v1/brand-specifications/${specId}/document`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(`Download fallito (${res.status})`);
  return res.blob();
}

// ── Vision capture / analyze ────────────────────────────────────────────────
export interface CaptureSessionLite {
  id: string;
  test_job_id: string;
  capture_type: string;
  batch_id: string | null;
  test_method_code: string | null;
}

export const createCaptureSession = (body: {
  test_job_id: string;
  batch_id?: string | null;
  test_method_code?: string | null;
  capture_type?: string;
  illuminant?: string | null;
  lightbox_ref_id?: string | null;
  grey_scale_ref_id?: string | null;
  white_tile_ref_id?: string | null;
  colour_target_ref_id?: string | null;
  has_inframe_grey_scale?: boolean;
  strict_quality?: boolean;
}) =>
  apiFetch<CaptureSessionLite>("/api/v1/capture-sessions", {
    method: "POST",
    body: JSON.stringify(body),
  });

export async function uploadCaptureImage(
  sessionId: string,
  file: File,
  assetType = "multifiber_after"
): Promise<void> {
  const token = getAccessToken();
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(
    `${API_BASE}/api/v1/capture-sessions/${sessionId}/images?asset_type=${encodeURIComponent(assetType)}`,
    { method: "POST", headers: token ? { Authorization: `Bearer ${token}` } : {}, body: fd }
  );
  if (!res.ok) throw new Error(`Upload immagine fallito (${res.status})`);
}

export const analyzeCaptureSession = (sessionId: string) =>
  apiFetch<MeasurementResult>(`/api/v1/capture-sessions/${sessionId}/analyze`, { method: "POST" });

// ── Calibration references (instruments + validity) ──────────────────────────
export const listCalibrationReferences = () =>
  apiFetch<CalibrationReference[]>("/api/v1/calibration-references");

export const createCalibrationReference = (body: {
  kind: string;
  code: string;
  description?: string | null;
  certificate_number?: string | null;
  valid_from?: string | null;
  valid_until?: string | null;
}) =>
  apiFetch<CalibrationReference>("/api/v1/calibration-references", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const retireCalibrationReference = (refId: string) =>
  apiFetch<CalibrationReference>(`/api/v1/calibration-references/${refId}/retire`, {
    method: "POST",
  });

// ── Batch zero ────────────────────────────────────────────────────────────────
export const listBatches = () => apiFetch<Batch[]>("/api/v1/multifiber-batches");

export const listStripProfiles = () =>
  apiFetch<StripProfile[]>("/api/v1/multifiber-batches/strip-profiles");

export const createBatch = (body: {
  batch_code: string;
  supplier?: string | null;
  strip_profile_code?: string | null;
  reference_lab_values: Record<string, LabValue>;
}) =>
  apiFetch<Batch>("/api/v1/multifiber-batches", { method: "POST", body: JSON.stringify(body) });

// ── Test methods + reference-norm documents ─────────────────────────────────
export const listTestMethods = () => apiFetch<TestMethod[]>("/api/v1/test-methods");

export interface MethodDocumentMeta {
  id: string;
  test_method_code: string;
  filename: string;
  sha256_hash: string;
  content_type: string | null;
}

export const listMethodDocuments = () =>
  apiFetch<MethodDocumentMeta[]>("/api/v1/test-methods/documents");

export async function uploadMethodDocument(code: string, file: File): Promise<MethodDocumentMeta> {
  const token = getAccessToken();
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${API_BASE}/api/v1/test-methods/${encodeURIComponent(code)}/document`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: fd,
  });
  if (!res.ok) throw new Error(`Upload norma fallito (${res.status})`);
  return res.json();
}

export async function downloadMethodDocument(code: string): Promise<Blob> {
  const token = getAccessToken();
  const res = await fetch(`${API_BASE}/api/v1/test-methods/${encodeURIComponent(code)}/document`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(`Download norma fallito (${res.status})`);
  return res.blob();
}

// ── Test jobs ─────────────────────────────────────────────────────────────────
export const listTestJobs = (params?: { status?: string }) => {
  const q = params?.status ? `?status=${encodeURIComponent(params.status)}` : "";
  return apiFetch<TestJob[]>(`/api/v1/test-jobs${q}`);
};

export const createTestJob = (body: {
  brand_specification_id?: string | null;
  test_method_code?: string | null;
  article_code?: string | null;
  lot_code?: string | null;
  barcode?: string | null;
  article_id?: string | null;
  article_variant_id?: string | null;
}) => apiFetch<TestJob>("/api/v1/test-jobs", { method: "POST", body: JSON.stringify(body) });

// ── Articles + variants (production-sample reference) ─────────────────────────
export const listArticles = () => apiFetch<Article[]>("/api/v1/articles");

export const getArticle = (id: string) => apiFetch<Article>(`/api/v1/articles/${id}`);

export const createArticle = (body: {
  code: string;
  name?: string | null;
  composition?: string | null;
  brand_specification_id?: string | null;
  variants?: {
    code: string;
    color_name?: string | null;
    lot_code?: string | null;
    reference_lab?: LabValue | null;
  }[];
}) => apiFetch<Article>("/api/v1/articles", { method: "POST", body: JSON.stringify(body) });

export const addVariant = (
  articleId: string,
  body: {
    code: string;
    color_name?: string | null;
    lot_code?: string | null;
    reference_lab?: LabValue | null;
  }
) =>
  apiFetch<ArticleVariant>(`/api/v1/articles/${articleId}/variants`, {
    method: "POST",
    body: JSON.stringify(body),
  });

export const listGradingProfiles = (params?: {
  standard_family?: string;
  assessment_type?: string;
}) => {
  const q = new URLSearchParams();
  if (params?.standard_family) q.set("standard_family", params.standard_family);
  if (params?.assessment_type) q.set("assessment_type", params.assessment_type);
  const qs = q.toString();
  return apiFetch<GradingProfile[]>(`/api/v1/articles/grading-profiles${qs ? `?${qs}` : ""}`);
};

export const getResults = (jobId: string) =>
  apiFetch<MeasurementResult[]>(`/api/v1/test-jobs/${jobId}/results`);

export const submitManualResult = (
  jobId: string,
  body: {
    test_method_code: string;
    fibers: Record<string, { delta_e?: number | null; gray_scale_grade?: number | null }>;
    notes?: string | null;
  }
) =>
  apiFetch<MeasurementResult>(`/api/v1/test-jobs/${jobId}/manual-result`, {
    method: "POST",
    body: JSON.stringify(body),
  });

export const generateReport = (jobId: string) =>
  apiFetch<Report>(`/api/v1/test-jobs/${jobId}/reports`, { method: "POST" });

// ── Reports / ledger ──────────────────────────────────────────────────────────
export const listReports = () => apiFetch<Report[]>("/api/v1/reports");

export const verifyReport = (reportId: string) =>
  apiFetch<ReportVerify>(`/api/v1/reports/${reportId}/verify`);

export const downloadReportUrl = (reportId: string) =>
  `${import.meta.env.VITE_API_BASE ?? "http://localhost:8000"}/api/v1/reports/${reportId}/download`;

export async function downloadReport(reportId: string): Promise<Blob> {
  const token = getAccessToken();
  const res = await fetch(downloadReportUrl(reportId), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(`Download failed (${res.status})`);
  return res.blob();
}

