import { apiFetch } from "./client";
import type { Role } from "@/lib/roles";

export interface Member {
  user_id: string;
  email: string;
  full_name: string | null;
  role: string;
  created_at: string;
}

export const listMembers = () => apiFetch<Member[]>("/api/v1/companies/members");

export const addMember = (body: {
  email: string;
  password: string;
  full_name?: string | null;
  role: Role;
}) =>
  apiFetch<Member>("/api/v1/companies/members", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const removeMember = (userId: string) =>
  apiFetch<void>(`/api/v1/companies/members/${userId}`, { method: "DELETE" });

// ── Operator authorizations (ISO 17025 §6.2 personnel register) ───────────────

export interface OperatorAuthorization {
  id: string;
  user_id: string;
  email: string;
  method_code: string | null;
  valid_from: string;
  valid_until: string | null;
  training_notes: string | null;
  status: string;
}

export const listAuthorizations = () =>
  apiFetch<OperatorAuthorization[]>("/api/v1/companies/authorizations");

export const addAuthorization = (body: {
  user_id: string;
  method_code?: string | null;
  valid_until?: string | null;
  training_notes?: string | null;
}) =>
  apiFetch<OperatorAuthorization>("/api/v1/companies/authorizations", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const revokeAuthorization = (id: string) =>
  apiFetch<void>(`/api/v1/companies/authorizations/${id}/revoke`, { method: "POST" });
