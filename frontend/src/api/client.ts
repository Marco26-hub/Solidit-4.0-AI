// Typed API client with silent token refresh on 401.
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

const ACCESS_KEY = "solidita.access_token";
const REFRESH_KEY = "solidita.refresh_token";
const PROFILE_KEY = "solidita.profile";

export function setTokens(access: string | null, refresh?: string | null): void {
  if (access) localStorage.setItem(ACCESS_KEY, access);
  else localStorage.removeItem(ACCESS_KEY);
  if (refresh !== undefined) {
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
    else localStorage.removeItem(REFRESH_KEY);
  }
}

// kept for backward compatibility (single-arg callers)
export function setAccessToken(token: string | null): void {
  setTokens(token);
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export interface ApiErrorBody {
  error: { code: string; message: string; details?: unknown };
}

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(status: number, body: ApiErrorBody) {
    super(body.error?.message ?? "Request failed");
    this.status = status;
    this.code = body.error?.code ?? "error";
  }
}

// ── silent refresh (single-flight) ──────────────────────────────────────────
// Our backend ROTATES refresh tokens and revokes the family on reuse, so two
// concurrent refreshes with the same token would self-revoke. We therefore
// share a single in-flight refresh across all callers.
let refreshInFlight: Promise<boolean> | null = null;

async function doRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  // preserve the selected tenant across refresh
  let companyId: string | null = null;
  const profileRaw = localStorage.getItem(PROFILE_KEY);
  if (profileRaw) {
    try {
      companyId = (JSON.parse(profileRaw)?.companyId as string | null) ?? null;
    } catch (e) {
      console.warn("doRefresh: corrupted profile in localStorage", e);
      companyId = null;
    }
  }

  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken, company_id: companyId }),
    });
    if (!res.ok) return false;
    const data = (await res.json()) as { access_token: string; refresh_token: string };
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch (e) {
    console.error("doRefresh: token refresh request failed", e);
    return false;
  }
}

function refreshOnce(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = doRefresh().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  _retried = false
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  // try a one-shot silent refresh on 401 (never for the auth endpoints themselves)
  if (res.status === 401 && !_retried && !path.startsWith("/api/v1/auth/")) {
    const refreshed = await refreshOnce();
    if (refreshed) return apiFetch<T>(path, init, true);
    clearTokens();
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event("solidita:unauthorized"));
    }
  }

  if (!res.ok) {
    const body = (await res.json().catch((e) => {
      console.warn("apiFetch: error body is not JSON", e, "status", res.status);
      return { error: { code: "error", message: res.statusText } };
    })) as ApiErrorBody;
    throw new ApiError(res.status, body);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
