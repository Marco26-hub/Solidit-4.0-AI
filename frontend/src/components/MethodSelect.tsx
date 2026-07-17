import { useMemo } from "react";

import type { TestMethod } from "@/api/types";

const SELECT_BASE =
  "w-full rounded-lg border border-slate-300 bg-white px-3 text-base text-ink outline-none transition focus:border-brand-500 min-h-[44px] sm:text-sm " +
  "appearance-none cursor-pointer bg-no-repeat pr-9 [background-position:right_0.6rem_center] " +
  "bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2216%22%20height%3D%2216%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23475569%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22/%3E%3C/svg%3E')]";

/** Collapse the fine standard_family label into one of the top-level norm bodies. */
export function normGroup(fam: string | null | undefined): string {
  const f = (fam ?? "").toUpperCase();
  // leather first (its ISO codes are 116xx/157xx/177xx, not ISO 105)
  if (f.includes("CUOIO") || f.includes("IULTCS") || f.includes("IUF") || f.includes("LEATHER"))
    return "Cuoio (ISO/IULTCS)";
  if (f.includes("AATCC")) return "AATCC";
  if (f.includes("ASTM")) return "ASTM";
  if (f.includes("ISO")) return "UNI EN ISO 105";
  return "Interni";
}

/** Display order of the norm bodies. */
export function groupRank(g: string): number {
  if (g === "UNI EN ISO 105") return 0;
  if (g === "AATCC") return 1;
  if (g === "ASTM") return 2;
  if (g === "Cuoio (ISO/IULTCS)") return 3;
  return 9;
}

/**
 * Method picker grouped by standard family (<optgroup>) with a human description
 * on every option. `value` is the method CODE.
 */
export function MethodSelect({
  methods,
  value,
  onChange,
  className = SELECT_BASE,
  emptyLabel = "— scegli metodo —",
  allowEmpty = true,
}: {
  methods: TestMethod[];
  value: string;
  onChange: (code: string) => void;
  className?: string;
  emptyLabel?: string;
  allowEmpty?: boolean;
}) {
  const groups = useMemo(() => {
    const g = new Map<string, TestMethod[]>();
    for (const m of methods) {
      const k = normGroup(m.standard_family);
      if (!g.has(k)) g.set(k, []);
      g.get(k)!.push(m);
    }
    for (const list of g.values()) list.sort((a, b) => a.code.localeCompare(b.code));
    return [...g.entries()].sort(
      (a, b) => groupRank(a[0]) - groupRank(b[0]) || a[0].localeCompare(b[0])
    );
  }, [methods]);

  return (
    <select className={className} value={value} onChange={(e) => onChange(e.target.value)}>
      {allowEmpty && <option value="">{emptyLabel}</option>}
      {groups.map(([family, list]) => (
        <optgroup key={family} label={family}>
          {list.map((m) => (
            <option key={m.id ? String(m.id) : m.code} value={m.code} title={m.name}>
              {m.code} — {m.name}
            </option>
          ))}
        </optgroup>
      ))}
    </select>
  );
}
