import { useMemo } from "react";

import type { TestMethod } from "@/api/types";

/** Family display order: ISO series first, then AATCC, ASTM, internal/other last. */
function familyRank(fam: string): number {
  if (fam.startsWith("ISO")) return 0;
  if (fam.startsWith("AATCC")) return 1;
  if (fam.startsWith("ASTM")) return 2;
  return 9; // internal / other
}

/**
 * Method picker grouped by standard family (<optgroup>) with a human description
 * on every option. `value` is the method CODE.
 */
export function MethodSelect({
  methods,
  value,
  onChange,
  className = "w-full rounded-lg border border-slate-300 px-2 py-1.5 text-sm min-h-[40px]",
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
      const k = m.standard_family ?? "Altro";
      if (!g.has(k)) g.set(k, []);
      g.get(k)!.push(m);
    }
    return [...g.entries()].sort(
      (a, b) => familyRank(a[0]) - familyRank(b[0]) || a[0].localeCompare(b[0])
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
