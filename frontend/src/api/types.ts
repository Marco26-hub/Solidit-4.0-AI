// Shared types mirroring the backend Pydantic schemas.

export interface CompanyBrief {
  id: string;
  name: string;
  role: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  company_id: string | null;
  role: string | null;
  companies: CompanyBrief[];
}

export interface Company {
  id: string;
  name: string;
  vat_number: string | null;
  account_tier: string;
  active_departments: Record<string, unknown>;
  settings: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: string;
  code: string;
  name: string;
  metadata: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Device {
  id: string;
  name: string;
  hardware_uuid: string;
  model: string | null;
  os_version: string | null;
  mdm_managed: boolean;
  calibration_profile: Record<string, unknown>;
  active_d65_matrix: Record<string, unknown> | null;
  active_tl84_matrix: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AcceptanceRule {
  id: string;
  test_method_code: string;
  fiber_code: string | null;
  max_delta_e: number | null;
  min_gray_scale_grade: number | null;
  severity: string;
  is_active: boolean;
}

export interface AcceptanceRuleInput {
  test_method_code: string;
  fiber_code?: string | null;
  max_delta_e?: number | null;
  min_gray_scale_grade?: number | null;
  severity: string;
}

export interface BrandSpec {
  id: string;
  brand_name: string;
  description: string | null;
  metadata: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  rules: AcceptanceRule[];
}

export interface LabValue {
  L: number;
  a: number;
  b: number;
}

export interface StripProfile {
  code: string;
  name: string;
  standard_family: string | null;
  fibers: string[];
}

export interface Batch {
  id: string;
  batch_code: string;
  supplier: string | null;
  strip_profile_code: string | null;
  opened_at: string | null;
  expires_at: string | null;
  reference_lab_values: Record<string, LabValue>;
  status: string;
  created_at: string;
}

export interface TestMethod {
  id: string;
  code: string;
  name: string;
  category: string;
  standard_family: string | null;
  metadata: Record<string, unknown>;
}

export interface ArticleVariant {
  id: string;
  article_id: string;
  code: string;
  color_name: string | null;
  lot_code: string | null;
  reference_lab: LabValue | null;
  is_active: boolean;
  created_at: string;
}

export interface Article {
  id: string;
  code: string;
  name: string | null;
  composition: string | null;
  brand_specification_id: string | null;
  is_active: boolean;
  created_at: string;
  variants: ArticleVariant[];
}

export interface GradingProfile {
  id: string;
  code: string;
  name: string;
  standard_family: string; // ISO_105 | AATCC | ASTM
  assessment_type: string; // staining | change
  thresholds: { max_delta_e: number; grade: number }[];
  is_builtin: boolean;
}

export interface TestJob {
  id: string;
  department_id: string | null;
  brand_specification_id: string | null;
  test_method_id: string | null;
  barcode: string | null;
  article_code: string | null;
  lot_code: string | null;
  article_id: string | null;
  article_variant_id: string | null;
  status: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface CalibrationReference {
  id: string;
  kind: string; // grey_scale | white_tile | colour_target | lightbox | other
  code: string;
  description: string | null;
  certificate_number: string | null;
  valid_from: string | null;
  valid_until: string | null;
  status: string;
  validity: string; // valid | expiring | expired | retired
  created_at: string;
}

export interface MeasurementResult {
  id: string;
  algorithm_version: string;
  results: Record<string, unknown>;
  pass_fail: {
    overall_pass: boolean;
    evaluated: boolean;
    per_fiber: Record<string, { pass: boolean; checks: unknown[] }>;
    violations: unknown[];
  };
  created_at: string;
}

export interface Report {
  id: string;
  report_number: string;
  test_job_id: string;
  sha256_hash: string;
  status: string;
  locked_at: string | null;
  created_at: string;
}

export interface ReportVerify {
  report_number: string;
  sha256_hash: string;
  recomputed_hash: string;
  valid: boolean;
}
