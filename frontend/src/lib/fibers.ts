import type { StripProfile, TestMethod } from "@/api/types";

export const ALL_FIBERS = [
  "acetate",
  "diacetate",
  "triacetate",
  "cotton",
  "nylon",
  "polyamide",
  "polyester",
  "acrylic",
  "wool",
  "silk",
  "viscose",
];

/** Map any standard label to the multifibre family key. */
export function fiberFamily(raw: string | null | undefined): string {
  const r = (raw ?? "").toUpperCase();
  if (r.includes("AATCC")) return "AATCC";
  if (r.includes("ASTM")) return "ASTM";
  if (r.includes("ISO")) return "ISO";
  return "OTHER";
}

/**
 * Fibres of the multifibre strip for the norm of `code` — the union of that
 * family's strip profiles (ISO→F10 DW∪TV, AATCC→No.1∪No.10). Falls back to all
 * fibres when no profile matches the norm.
 */
export function fibersForMethod(
  code: string,
  methods: TestMethod[],
  profiles: StripProfile[]
): string[] {
  const m = methods.find((x) => x.code === code);
  const fam = fiberFamily(m?.standard_family);
  const set = new Set<string>();
  for (const p of profiles) {
    if (fiberFamily(p.standard_family) === fam) p.fibers.forEach((f) => set.add(f));
  }
  return set.size ? [...set] : ALL_FIBERS;
}
