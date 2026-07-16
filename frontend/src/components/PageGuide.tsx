import type { ReactNode } from "react";

// Plain-language, step-by-step guide for the inexperienced operator.
// Collapsible so experts aren't cluttered; pass defaultOpen (e.g. when the
// page's main list is still empty) to open it for first-time users.
export function PageGuide({
  steps,
  defaultOpen = false,
  title = "Guida rapida — cosa fare in questa pagina",
}: {
  steps: ReactNode[];
  defaultOpen?: boolean;
  title?: string;
}) {
  return (
    <details
      open={defaultOpen}
      className="mb-4 rounded-xl border border-brand-200 bg-brand-50/60 px-4 py-1"
    >
      <summary className="cursor-pointer select-none py-2 text-sm font-medium text-brand-700">
        {title}
      </summary>
      <ol className="mb-3 mt-1 space-y-2">
        {steps.map((s, i) => (
          <li key={i} className="flex gap-2 text-sm leading-relaxed text-steel">
            <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-600 text-[11px] font-bold text-white">
              {i + 1}
            </span>
            <span>{s}</span>
          </li>
        ))}
      </ol>
    </details>
  );
}
