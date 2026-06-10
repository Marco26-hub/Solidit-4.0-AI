import { apiFetch } from "./client";
import type { Company, Department, Device } from "./types";

export const getMyCompany = () => apiFetch<Company>("/api/v1/companies/me");

export const listDepartments = () => apiFetch<Department[]>("/api/v1/departments");

export const createDepartment = (body: { code: string; name: string }) =>
  apiFetch<Department>("/api/v1/departments", { method: "POST", body: JSON.stringify(body) });

export const listDevices = () => apiFetch<Device[]>("/api/v1/devices");

export const registerDevice = (body: {
  hardware_uuid: string;
  model?: string | null;
  name?: string | null;
  mdm_managed?: boolean;
}) =>
  apiFetch<Device>("/api/v1/devices/register", { method: "POST", body: JSON.stringify(body) });
