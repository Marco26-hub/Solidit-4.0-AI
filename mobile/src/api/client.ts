// Typed API client (mobile). Token stored in secure storage in Sprint 6.
const API_BASE = process.env.EXPO_PUBLIC_API_BASE ?? "http://localhost:8000";

let accessToken: string | null = null;
export function setAccessToken(t: string | null) {
  accessToken = t;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return (await res.json()) as T;
}
