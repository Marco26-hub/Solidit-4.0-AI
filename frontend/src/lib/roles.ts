// Role helpers mirroring the backend authorization rules:
// - operator: creates prove/catture/analisi/risultati
// - lab_manager: operator + generates/finalizes reports + manages configuration
//   (capitolati, batch, tarature, articoli, validazione)
// - company_admin: lab_manager + team & company settings
import { useAuth } from "@/lib/auth";

export type Role = "operator" | "lab_manager" | "company_admin";

export const ROLE_LABELS: Record<Role, string> = {
  operator: "Operatore",
  lab_manager: "Manager",
  company_admin: "Amministratore",
};

export function roleLabel(role: string | null): string {
  return role && role in ROLE_LABELS ? ROLE_LABELS[role as Role] : (role ?? "—");
}

// Pure predicates (usable outside React) — keep in sync with backend deps.
export const can = {
  /** prove, catture, analisi, risultati — all three roles */
  canOperate: (role: string | null): boolean =>
    role === "operator" || role === "lab_manager" || role === "company_admin",
  /** report generate/finalize + capitolati/batch/tarature/articoli/validazione writes */
  canManage: (role: string | null): boolean =>
    role === "lab_manager" || role === "company_admin",
  /** team + company settings */
  canAdmin: (role: string | null): boolean => role === "company_admin",
} as const;

export function useRole(): {
  role: string | null;
  canOperate: boolean;
  canManage: boolean;
  canAdmin: boolean;
} {
  const { profile } = useAuth();
  const role = profile?.role ?? null;
  return {
    role,
    canOperate: can.canOperate(role),
    canManage: can.canManage(role),
    canAdmin: can.canAdmin(role),
  };
}
