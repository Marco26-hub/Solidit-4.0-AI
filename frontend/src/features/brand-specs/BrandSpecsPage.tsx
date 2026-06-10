import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createBrandSpec,
  downloadCapitolato,
  listBrandSpecs,
  listStripProfiles,
  listTestMethods,
  uploadCapitolato,
} from "@/api/quality";
import type { AcceptanceRuleInput } from "@/api/types";
import { MethodSelect } from "@/components/MethodSelect";
import { Badge, Button, Card, EmptyState, ErrorText, Field, PageHeader, TextInput } from "@/components/ui";
import { ALL_FIBERS, fibersForMethod } from "@/lib/fibers";

const emptyRule = (): AcceptanceRuleInput => ({
  test_method_code: "",
  fiber_code: null,
  max_delta_e: null,
  min_gray_scale_grade: null,
  severity: "blocking",
});

const numOrNull = (v: string): number | null => (v === "" ? null : Number(v));

// Parse a pasted capitolato CSV (Italian Excel ';' + decimal comma) into rules.
function parseCsvRules(text: string): AcceptanceRuleInput[] {
  const t = text.trim();
  if (!t) return [];
  const lines = t.split(/\r?\n/).filter((l) => l.trim());
  const first = lines[0];
  const delim = (first.split(";").length - 1) >= (first.split(",").length - 1) ? ";" : ",";
  const head = (lines[0].split(delim)[0] ?? "").toLowerCase();
  const body =
    head.includes("metodo") || head.includes("method") || head.includes("test")
      ? lines.slice(1)
      : lines;
  const num = (s?: string): number | null => {
    if (!s) return null;
    const n = Number(s.replace(",", "."));
    return Number.isNaN(n) ? null : n;
  };
  return body
    .map((l) => l.split(delim).map((c) => c.trim()))
    .filter((c) => c[0])
    .map((c) => ({
      test_method_code: c[0],
      fiber_code: c[1] || null,
      max_delta_e: num(c[2]),
      min_gray_scale_grade: num(c[3]),
      severity: (c[4] || "blocking").toLowerCase() === "warning" ? "warning" : "blocking",
    }));
}

export function BrandSpecsPage() {
  const qc = useQueryClient();
  const specs = useQuery({ queryKey: ["brand-specs"], queryFn: listBrandSpecs });
  const methods = useQuery({ queryKey: ["test-methods"], queryFn: listTestMethods });
  const profiles = useQuery({ queryKey: ["strip-profiles"], queryFn: listStripProfiles });

  const [brandName, setBrandName] = useState("");
  const [desc, setDesc] = useState("");
  const [rules, setRules] = useState<AcceptanceRuleInput[]>([emptyRule()]);
  const [csv, setCsv] = useState("");
  const [uploading, setUploading] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () =>
      createBrandSpec({
        brand_name: brandName,
        description: desc || null,
        rules: rules.filter((r) => r.test_method_code),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["brand-specs"] });
      setBrandName("");
      setDesc("");
      setRules([emptyRule()]);
      setCsv("");
    },
  });

  const setRule = (i: number, patch: Partial<AcceptanceRuleInput>) =>
    setRules((rs) => rs.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));

  function importCsv() {
    const parsed = parseCsvRules(csv);
    if (parsed.length) setRules(parsed);
  }

  async function attach(specId: string, file: File) {
    setUploading(specId);
    try {
      await uploadCapitolato(specId, file);
      qc.invalidateQueries({ queryKey: ["brand-specs"] });
    } finally {
      setUploading(null);
    }
  }

  async function download(specId: string, name: string) {
    const blob = await downloadCapitolato(specId);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Brand Specs" subtitle="Capitolati brand e regole di accettazione" />

      <Card>
        <div className="mb-2 font-medium">Specifiche esistenti</div>
        {specs.isLoading && <p className="text-steel">Caricamento…</p>}
        <ErrorText error={specs.error} />
        <div className="divide-y">
          {(specs.data ?? []).map((s) => {
            const doc = (s.metadata as Record<string, { filename?: string }> | undefined)
              ?.capitolato_document;
            return (
              <div key={s.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                <div>
                  <div className="font-medium">{s.brand_name}</div>
                  <div className="text-steel">{s.rules.length} regole</div>
                </div>
                <div className="flex items-center gap-2">
                  {doc ? (
                    <Button variant="ghost" onClick={() => download(s.id, doc.filename ?? "capitolato")}>
                      📎 capitolato
                    </Button>
                  ) : (
                    <label className="cursor-pointer rounded-lg border border-slate-200 px-3 py-2 text-sm text-steel hover:bg-slate-50">
                      {uploading === s.id ? "…" : "Allega PDF"}
                      <input
                        type="file"
                        accept="application/pdf"
                        className="hidden"
                        onChange={(e) => e.target.files?.[0] && attach(s.id, e.target.files[0])}
                      />
                    </label>
                  )}
                  <Badge kind={s.is_active ? "pass" : "muted"}>{s.is_active ? "attivo" : "off"}</Badge>
                </div>
              </div>
            );
          })}
          {specs.data?.length === 0 && (
            <EmptyState title="Nessuna brand spec" hint="Crea il primo capitolato qui sotto." />
          )}
        </div>
      </Card>

      <Card>
        <div className="mb-3 font-medium">Nuova brand spec</div>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Brand">
            <TextInput value={brandName} onChange={(e) => setBrandName(e.target.value)} placeholder="Zara" />
          </Field>
          <Field label="Descrizione">
            <TextInput value={desc} onChange={(e) => setDesc(e.target.value)} />
          </Field>
        </div>

        <div className="mt-4">
          <Field label="Importa capitolato (CSV: metodo;fibra;maxΔE;minGrey;severità)">
            <textarea
              className="h-20 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs"
              placeholder={"ISO_105_X12;cotton;1,0;4,0;blocking\nISO_105_C06;;0,8;;warning"}
              value={csv}
              onChange={(e) => setCsv(e.target.value)}
            />
          </Field>
          <div className="mt-2">
            <Button variant="ghost" type="button" disabled={!csv.trim()} onClick={importCsv}>
              ↧ Importa nelle regole
            </Button>
          </div>
        </div>

        <div className="mt-4 text-sm font-medium">Regole di accettazione</div>
        <div className="mt-2 space-y-2">
          {rules.map((r, i) => {
            // fibres shown follow the multifibre of the rule's norm (all of them);
            // default "tutte le fibre" — the operator no longer picks generic single fibres
            const ruleFibers = r.test_method_code
              ? fibersForMethod(r.test_method_code, methods.data ?? [], profiles.data ?? [])
              : ALL_FIBERS;
            return (
            <div key={i} className="grid grid-cols-2 gap-2 md:grid-cols-6">
              <MethodSelect
                className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm min-h-[40px]"
                methods={methods.data ?? []}
                value={r.test_method_code}
                emptyLabel="metodo…"
                onChange={(code) =>
                  // changing the norm resets the fibre to "tutte le fibre" (norm's multifibre)
                  setRule(i, { test_method_code: code, fiber_code: null })
                }
              />
              <select
                className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
                value={r.fiber_code ?? ""}
                onChange={(e) => setRule(i, { fiber_code: e.target.value || null })}
              >
                <option value="">tutte le fibre (multifibra norma)</option>
                {ruleFibers.map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
              <TextInput
                type="number"
                step="0.01"
                placeholder="max ΔE"
                value={r.max_delta_e ?? ""}
                onChange={(e) => setRule(i, { max_delta_e: numOrNull(e.target.value) })}
              />
              <TextInput
                type="number"
                step="0.5"
                placeholder="min grey"
                value={r.min_gray_scale_grade ?? ""}
                onChange={(e) => setRule(i, { min_gray_scale_grade: numOrNull(e.target.value) })}
              />
              <select
                className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
                value={r.severity}
                onChange={(e) => setRule(i, { severity: e.target.value })}
              >
                <option value="blocking">blocking</option>
                <option value="warning">warning</option>
              </select>
              <Button variant="ghost" type="button" onClick={() => setRules((rs) => rs.filter((_, idx) => idx !== i))}>
                ✕
              </Button>
            </div>
            );
          })}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button variant="ghost" type="button" onClick={() => setRules((rs) => [...rs, emptyRule()])}>
            + regola
          </Button>
          <Button type="button" disabled={!brandName || create.isPending} onClick={() => create.mutate()}>
            {create.isPending ? "…" : "Crea brand spec"}
          </Button>
        </div>
        <ErrorText error={create.error} />
      </Card>
    </div>
  );
}
