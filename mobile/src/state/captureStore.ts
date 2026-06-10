// Centralized capture state (from MOBILE_APP_SPEC.md). The physical dima
// guarantees distance; LiDAR/ToF is only a coherence check. In metrological
// mode, manual capture is blocked until all gates pass.

export type Telemetry = {
  tiltDeg: number;
  distanceMm?: number;
  blurScore: number;
  exposureScore: number;
  motionScore: number;
};

export type CaptureState = {
  companyId: string;
  departmentId: string;
  deviceId: string;
  testJobId: string;
  selectedWorkflow: string;
  telemetry: Telemetry;
  captureReady: boolean;
  errors: string[];
};

export const initialCaptureState: CaptureState = {
  companyId: "",
  departmentId: "",
  deviceId: "",
  testJobId: "",
  selectedWorkflow: "",
  telemetry: { tiltDeg: 0, blurScore: 0, exposureScore: 0, motionScore: 0 },
  captureReady: false,
  errors: [],
};

// Pure gate evaluation — capture is allowed only when every condition is OK.
export function evaluateCaptureGates(t: Telemetry): { ready: boolean; errors: string[] } {
  const errors: string[] = [];
  if (Math.abs(t.tiltDeg) > 3) errors.push("tilt");
  if (t.blurScore < 0.8) errors.push("blur");
  if (t.exposureScore < 0.8) errors.push("exposure");
  if (t.motionScore > 0.2) errors.push("motion");
  return { ready: errors.length === 0, errors };
}
