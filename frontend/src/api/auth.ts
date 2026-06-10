import { apiFetch } from "./client";
import type { TokenResponse } from "./types";

export function login(email: string, password: string, companyId?: string) {
  return apiFetch<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password, company_id: companyId ?? null }),
  });
}

export function selectCompany(companyId: string) {
  return apiFetch<TokenResponse>("/api/v1/auth/select-company", {
    method: "POST",
    body: JSON.stringify({ company_id: companyId }),
  });
}
