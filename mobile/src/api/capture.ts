// Capture flow against the Solidità backend: create a capture session, upload
// the multifibre photo, then run analysis. Mirrors the web client + the
// backend /api/v1/capture-sessions endpoints.
import { apiFetch } from "./client";

const API_BASE = process.env.EXPO_PUBLIC_API_BASE ?? "http://localhost:8000";

export interface CaptureSessionInput {
  test_job_id: string;
  batch_id?: string | null;
  test_method_code?: string | null;
  capture_type?: string; // multifiber_after | colour_change
  illuminant?: string | null;
  lightbox_ref_id?: string | null;
  grey_scale_ref_id?: string | null;
  has_inframe_grey_scale?: boolean;
  strict_quality?: boolean;
}

export interface CaptureSession {
  id: string;
  test_job_id: string;
  capture_type: string;
}

export interface MeasurementResult {
  id: string;
  algorithm_version: string;
  results: Record<string, unknown>;
  pass_fail: { overall_pass: boolean; evaluated: boolean };
}

export const createCaptureSession = (body: CaptureSessionInput) =>
  apiFetch<CaptureSession>("/api/v1/capture-sessions", {
    method: "POST",
    body: JSON.stringify(body),
  });

/** Upload a photo taken by vision-camera (a local file:// path). */
export async function uploadCaptureImage(
  sessionId: string,
  filePath: string,
  assetType = "multifiber_after",
  token?: string | null
): Promise<void> {
  const uri = filePath.startsWith("file://") ? filePath : `file://${filePath}`;
  const form = new FormData();
  // RN FormData file shape
  form.append("file", {
    uri,
    name: "capture.jpg",
    type: "image/jpeg",
  } as unknown as Blob);

  const res = await fetch(
    `${API_BASE}/api/v1/capture-sessions/${sessionId}/images?asset_type=${encodeURIComponent(
      assetType
    )}`,
    {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body: form,
    }
  );
  if (!res.ok) throw new Error(`Upload immagine fallito (${res.status})`);
}

export const analyzeCaptureSession = (sessionId: string) =>
  apiFetch<MeasurementResult>(`/api/v1/capture-sessions/${sessionId}/analyze`, {
    method: "POST",
  });
