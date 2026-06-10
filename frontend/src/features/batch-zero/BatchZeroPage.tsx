import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createBatch, listBatches, listStripProfiles } from "@/api/quality";
import type { LabValue } from "@/api/types";
import { Badge, Button, Card, EmptyState, ErrorText, Field, PageHeader, TextInput } from "@/components/ui";

type Cell = { L: string; a: string; b: string };

export function BatchZeroPage() {
  const qc = useQueryClient();
  const batches = useQuery({ queryKey: ["batches"], queryFn: listBatches });
  const profiles = useQuery({ queryKey: ["strip-profiles"], queryFn: listStripProfiles });

  const [code, setCode] = useState("");
  const [supplier, setSupplier] = useState("");
  const [stripCode, setStripCode] = useState<string>("");
  const [grid, setGrid] = useState<Record<string, Cell>>({});

  // fibres come from the SELECTED strip standard (AATCC vs ISO/UNI EN ISO 105-F10 DW/TV)
  const fibers = useMemo(() => {
    const p = profiles.data?.find((x) => x.code === stripCode);
    return p?.fibers ?? [];
  }, [profiles.data, stripCode]);

  const create = useMutation({
    mutationFn: () => {
      const ref: Record<string, LabValue> = {};
      for (const f of fibers) {
        const c = grid[f];
        if (c && c.L !== "" && c.a !== "" && c.b !== "") {
          ref[f] = { L: Number(c.L), a: Number(c.a), b: Number(c.b) };
        }
      }
      return createBatch({
        batch_code: code,
        supplier: supplier || null,
        strip_profile_code: stripCode || null,
        reference_lab_values: ref,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["batches"] });
      setCode("");
      setSupplier("");
      setGrid({});
    },
  });

  const set = (f: string, k: keyof Cell, v: string) =>
    setGrid((g) => ({ ...g, [f]: { ...(g[f] ?? { L: "", a: "", b: "" }), [k]: v } }));

  const hasAny = fibers.some((f) => grid[f]?.L && grid[f]?.a && grid[f]?.b);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Batch Zero"
        subtitle="Striscia multifibra di riferimento — valori Lab per fibra (lo standard sceglie le fibre)"
      />

      <Card>
        <div className="mb-2 font-medium">Batch registrati</div>
        <ErrorText error={batches.error} />
        <div className="divide-y">
          {(batches.data ?? []).map((b) => (
            <div key={b.id} className="flex items-center justify-between py-2 text-sm">
              <div>
                <div className="font-medium">{b.batch_code}</div>
                <div className="text-steel">
                  {b.strip_profile_code ?? "—"} · {Object.keys(b.reference_lab_values).length} fibre
                </div>
              </div>
              <Badge kind={b.status === "active" ? "pass" : "muted"}>{b.status}</Badge>
            </div>
          ))}
          {batches.data?.length === 0 && (
            <EmptyState title="Nessun batch zero" hint="Crea la prima striscia di riferimento qui sotto." />
          )}
        </div>
      </Card>

      <Card>
        <div className="mb-3 font-medium">Nuovo batch zero</div>
        <div className="grid gap-3 sm:grid-cols-3">
          <Field label="Codice batch">
            <TextInput value={code} onChange={(e) => setCode(e.target.value)} />
          </Field>
          <Field label="Fornitore">
            <TextInput value={supplier} onChange={(e) => setSupplier(e.target.value)} />
          </Field>
          <Field label="Standard striscia">
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm min-h-[40px]"
              value={stripCode}
              onChange={(e) => setStripCode(e.target.value)}
            >
              <option value="">— scegli —</option>
              {(profiles.data ?? []).map((p) => (
                <option key={p.code} value={p.code}>
                  {p.name}
                </option>
              ))}
            </select>
          </Field>
        </div>

        {fibers.length > 0 ? (
          <>
            <div className="mt-4 text-sm font-medium">Valori Lab per fibra ({stripCode})</div>
            <div className="mt-2 space-y-1">
              <div className="grid grid-cols-4 gap-2 text-xs text-steel">
                <span>Fibra</span>
                <span>L</span>
                <span>a</span>
                <span>b</span>
              </div>
              {fibers.map((f) => (
                <div key={f} className="grid grid-cols-4 gap-2">
                  <span className="self-center text-sm capitalize">{f}</span>
                  {(["L", "a", "b"] as const).map((k) => (
                    <TextInput
                      key={k}
                      type="number"
                      step="0.1"
                      value={grid[f]?.[k] ?? ""}
                      onChange={(e) => set(f, k, e.target.value)}
                    />
                  ))}
                </div>
              ))}
            </div>
          </>
        ) : (
          <p className="mt-4 text-sm text-steel">
            Scegli lo standard striscia per inserire i valori Lab delle fibre.
          </p>
        )}

        <div className="mt-3">
          <Button
            type="button"
            disabled={!code || !stripCode || !hasAny || create.isPending}
            onClick={() => create.mutate()}
          >
            {create.isPending ? "…" : "Crea batch zero"}
          </Button>
        </div>
        <ErrorText error={create.error} />
      </Card>
    </div>
  );
}
