import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-slate-200 bg-white p-4 shadow-card ${className}`}>
      {children}
    </div>
  );
}

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-4">
      <h1 className="text-xl font-semibold tracking-tight text-ink sm:text-2xl">{title}</h1>
      {subtitle && <p className="mt-0.5 text-sm text-steel">{subtitle}</p>}
    </div>
  );
}

export function Button({
  children,
  variant = "primary",
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" | "danger" }) {
  const base =
    "inline-flex items-center justify-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium transition active:scale-[.98] disabled:opacity-50 disabled:active:scale-100 min-h-[40px]";
  const styles = {
    primary: `${base} bg-brand-600 text-white hover:bg-brand-700`,
    ghost: `${base} border border-slate-200 text-steel hover:bg-slate-50`,
    danger: `${base} bg-red-600 text-white hover:bg-red-700`,
  } as const;
  return (
    <button className={styles[variant]} {...rest}>
      {children}
    </button>
  );
}

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 min-h-[40px]"
      {...props}
    />
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-steel">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

const BADGE = {
  pass: "bg-emerald-100 text-emerald-800",
  fail: "bg-red-100 text-red-700",
  warn: "bg-amber-100 text-amber-800",
  muted: "bg-slate-100 text-slate-600",
} as const;

export function Badge({
  kind,
  children,
}: {
  kind: keyof typeof BADGE;
  children: ReactNode;
}) {
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${BADGE[kind]}`}>
      {children}
    </span>
  );
}

export function statusBadgeKind(status: string): keyof typeof BADGE {
  if (status === "passed") return "pass";
  if (status === "failed") return "fail";
  if (status === "completed") return "warn";
  return "muted";
}

export function Stat({
  label,
  value,
  hint,
  icon,
  tone = "brand",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
  tone?: "brand" | "emerald" | "amber" | "slate";
}) {
  const tones = {
    brand: "bg-brand-50 text-brand-600",
    emerald: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
    slate: "bg-slate-100 text-slate-600",
  } as const;
  return (
    <Card>
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-steel">{label}</div>
          <div className="mt-1 text-2xl font-semibold text-ink">{value}</div>
          {hint && <div className="mt-0.5 text-xs text-steel">{hint}</div>}
        </div>
        {icon && (
          <span className={`grid h-9 w-9 place-items-center rounded-lg ${tones[tone]}`}>{icon}</span>
        )}
      </div>
    </Card>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50/60 px-4 py-8 text-center">
      <p className="text-sm font-medium text-steel">{title}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

export function Spinner() {
  return (
    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
  );
}

export function ErrorText({ error }: { error: unknown }) {
  if (!error) return null;
  const msg = error instanceof Error ? error.message : String(error);
  return <p className="text-sm text-red-600">{msg}</p>;
}
