// Operator auth: log in, persist the access token in the device secure store,
// and prime the API client. Token is sent as Bearer by apiFetch / uploads.
import * as SecureStore from "expo-secure-store";

import { apiFetch, setAccessToken } from "./client";

const TOKEN_KEY = "solidita.access_token";

export interface CompanyBrief {
  id: string;
  name: string;
  role: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  company_id: string | null;
  role: string | null;
  companies: CompanyBrief[];
}

export async function login(
  email: string,
  password: string,
  companyId?: string | null
): Promise<LoginResponse> {
  const res = await apiFetch<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password, company_id: companyId ?? null }),
  });
  setAccessToken(res.access_token);
  await SecureStore.setItemAsync(TOKEN_KEY, res.access_token);
  return res;
}

/** Restore a persisted session on app start. Returns true if a token was found. */
export async function restoreSession(): Promise<boolean> {
  const t = await SecureStore.getItemAsync(TOKEN_KEY);
  if (t) {
    setAccessToken(t);
    return true;
  }
  return false;
}

export async function logout(): Promise<void> {
  setAccessToken(null);
  await SecureStore.deleteItemAsync(TOKEN_KEY);
}
