import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
} from "react";

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
  className = "",
  loading = false,
  disabled,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "danger";
  loading?: boolean;
}) {
  const base =
    "inline-flex items-center justify-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium transition active:scale-[.98] disabled:opacity-50 disabled:active:scale-100 min-h-[44px]";
  const styles = {
    primary: `${base} bg-brand-600 text-white hover:bg-brand-700`,
    ghost: `${base} border border-slate-200 text-steel hover:bg-slate-50`,
    danger: `${base} bg-red-600 text-white hover:bg-red-700`,
  } as const;
  return (
    <button className={`${styles[variant]} ${className}`} disabled={disabled || loading} {...rest}>
      {loading && <Spinner />}
      {children}
    </button>
  );
}

const FIELD_BASE =
  "w-full rounded-lg border border-slate-300 bg-white px-3 text-base text-ink outline-none transition focus:border-brand-500 min-h-[44px] sm:text-sm";

// Native selects render their value with the platform text colour and truncate
// silently when cramped. Force dark text, add breathing room + an explicit
// chevron so every dropdown reads as an obvious, legible control.
const SELECT_CHEVRON =
  "appearance-none bg-no-repeat pr-9 cursor-pointer " +
  "bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2216%22%20height%3D%2216%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23475569%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22/%3E%3C/svg%3E')] " +
  "[background-position:right_0.6rem_center]";

export function TextInput({ className = "", ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`${FIELD_BASE} py-2 ${className}`} {...props} />;
}

export function Select({ className = "", children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={`${FIELD_BASE} ${SELECT_CHEVRON} ${className}`} {...props}>
      {children}
    </select>
  );
}

export function Field({
  label,
  children,
  hint,
  error,
  required = false,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
  error?: string;
  required?: boolean;
}) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-steel">
        {label}
        {required && <span className="ml-0.5 text-red-600">*</span>}
      </span>
      <div className="mt-1">{children}</div>
      {hint && !error && <p className="mt-1 text-xs text-steel">{hint}</p>}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </label>
  );
}

/** A muted one-line reason shown under a disabled primary action. */
export function Hint({ children }: { children: ReactNode }) {
  return <p className="mt-2 text-xs text-steel">{children}</p>;
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
