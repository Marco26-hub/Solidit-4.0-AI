import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createBatch, listBatches, listStripProfiles } from "@/api/quality";
import type { LabValue } from "@/api/types";
import { PageGuide } from "@/components/PageGuide";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorText,
  Field,
  Hint,
  PageHeader,
  Select,
  TextInput,
} from "@/components/ui";

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
        title="Batch Zero (striscia di riferimento)"
        subtitle="Striscia multifibra di riferimento — valori Lab per fibra (lo standard sceglie le fibre)"
      />

      <PageGuide
        defaultOpen={batches.isSuccess && batches.data.length === 0}
        steps={[
          <>La <b>striscia multifibra di riferimento</b> ("batch zero") è la striscia NON trattata: il colore pulito di partenza con cui si confronta la macchia. Registrala <b>prima</b> della prima prova di macchia.</>,
          <>Scegli lo <b>standard della striscia</b> (es. ISO 105-F10 DW): decide quali fibre contiene e in che ordine.</>,
          <>Inserisci i valori <b>Lab</b> per fibra: sono le coordinate del colore (L = chiaro/scuro, a = verde↔rosso, b = blu↔giallo). Li trovi sul certificato del lotto, oppure misurali su striscia nuova.</>,
          <>Un batch per lotto di strisce: quando apri una scatola nuova, registra un nuovo batch.</>,
        ]}
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
              <Badge kind={b.status === "active" ? "pass" : "muted"}>
                {b.status === "active" ? "Attivo" : b.status}
              </Badge>
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
          <Field label="Codice batch" required hint="Etichetta interna del lotto, es. BZ-2026-01.">
            <TextInput value={code} onChange={(e) => setCode(e.target.value)} placeholder="es. BZ-2026-01" />
          </Field>
          <Field label="Fornitore">
            <TextInput value={supplier} onChange={(e) => setSupplier(e.target.value)} />
          </Field>
          <Field label="Standard striscia" required hint="Determina quali fibre compongono la striscia.">
            <Select value={stripCode} onChange={(e) => setStripCode(e.target.value)}>
              <option value="">— scegli —</option>
              {(profiles.data ?? []).map((p) => (
                <option key={p.code} value={p.code}>
                  {p.name}
                </option>
              ))}
            </Select>
          </Field>
        </div>

        {fibers.length > 0 ? (
          <>
            <div className="mt-4 text-sm font-medium">Valori Lab per fibra ({stripCode})</div>
            <p className="mt-1 text-xs text-steel">
              Valori L*a*b* del colore di riferimento di ogni fibra, presi dallo strumento (L 0–100).
              Compila almeno una fibra per salvare.
            </p>
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
            loading={create.isPending}
            disabled={!code || !stripCode || !hasAny}
            onClick={() => create.mutate()}
          >
            Crea batch zero
          </Button>
          {(!code || !stripCode || !hasAny) && (
            <Hint>
              Per salvare: inserisci il codice batch, scegli lo standard striscia e compila il Lab di
              almeno una fibra.
            </Hint>
          )}
        </div>
        <ErrorText error={create.error} />
      </Card>
    </div>
  );
}
