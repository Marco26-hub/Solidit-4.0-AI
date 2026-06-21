import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { metamerism, type MetamerismResult } from "@/api/spectral";
import { Button, Card, ErrorText, Field, TextInput } from "@/components/ui";

const clamp = (v: number, lo: number, hi: number) => Math.min(Math.max(v, lo), hi);

// Two-sample metamerism comparison from ESTIMATED spectra (project rule 7).
// It can NOT reveal real metamerism between samples that match under the
// reference light — that needs measured spectra. The backend flags this.

type LabState = { L: string; a: string; b: string };

function LabFields({
  legend,
  lab,
  set,
}: {
  legend: string;
  lab: LabState;
  set: (patch: Partial<LabState>) => void;
}) {
  return (
    <div>
      <div className="mb-2 text-xs font-medium uppercase tracking-wide text-steel">{legend}</div>
      <div className="grid grid-cols-3 gap-2">
        <Field label="L">
          <TextInput
            type="number"
            inputMode="decimal"
            step="0.1"
            value={lab.L}
            onChange={(e) => set({ L: e.target.value })}
          />
        </Field>
        <Field label="a">
          <TextInput
            type="number"
            inputMode="decimal"
            step="0.1"
            value={lab.a}
            onChange={(e) => set({ a: e.target.value })}
          />
        </Field>
        <Field label="b">
          <TextInput
            type="number"
            inputMode="decimal"
            step="0.1"
            value={lab.b}
            onChange={(e) => set({ b: e.target.value })}
          />
        </Field>
      </div>
    </div>
  );
}

function numericLab(s: LabState) {
  return {
    L: clamp(Number(s.L) || 0, 0, 100),
    a: clamp(Number(s.a) || 0, -128, 128),
    b: clamp(Number(s.b) || 0, -128, 128),
  };
}

function Results({ data }: { data: MetamerismResult }) {
  return (
    <div className="mt-4 space-y-3">
      {data.warnings.length > 0 && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-xs leading-relaxed text-amber-800">
          <div className="font-semibold">Limite del metodo</div>
          {data.warnings.map((w, i) => (
            <p key={i} className="mt-1">
              {w}
            </p>
          ))}
        </div>
      )}

      <div className="text-sm">
        ΔE sotto {data.reference_illuminant} (riferimento):{" "}
        <span className="font-semibold text-ink">{data.delta_e_reference.toFixed(2)}</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[360px] text-sm">
          <thead className="text-left text-steel">
            <tr>
              <th className="py-1">Luce</th>
              <th>ΔE</th>
              <th>Indice metamerismo</th>
            </tr>
          </thead>
          <tbody>
            {data.per_illuminant.map((row) => (
              <tr key={row.illuminant} className="border-t">
                <td className="py-1.5 font-medium text-ink">{row.illuminant}</td>
                <td>{row.delta_e.toFixed(2)}</td>
                <td className={row.metamerism_index > 1 ? "font-semibold text-amber-700" : ""}>
                  {row.metamerism_index.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-steel">
        Indice = differenza di colore residua sotto la luce di prova, una volta annullato lo scarto
        sotto il riferimento (più alto = i due campioni divergono di più cambiando luce). Valore{" "}
        <b>STIMATO</b>, indicativo.
      </p>
    </div>
  );
}

export function MetamerismPanel() {
  const [ref, setRef] = useState<LabState>({ L: "45", a: "60", b: "35" });
  const [smp, setSmp] = useState<LabState>({ L: "45", a: "55", b: "48" });

  const run = useMutation({
    mutationFn: () =>
      metamerism({ lab_reference: numericLab(ref), lab_sample: numericLab(smp) }),
  });

  return (
    <Card>
      <div className="mb-1 font-medium">Metamerismo tra 2 campioni (STIMATO)</div>
      <p className="mb-3 text-xs leading-relaxed text-steel">
        Confronta riferimento e campione sotto luce diversa, a partire dai loro CIELAB. È{" "}
        <b>indicativo</b>: le curve sono stimate, quindi due campioni che combaciano sotto la luce
        di riferimento risultano identici e il metamerismo reale <b>non</b> è rilevabile (servono
        spettri misurati).
      </p>
      <div className="grid gap-4 md:grid-cols-2">
        <LabFields legend="Riferimento" lab={ref} set={(p) => setRef((s) => ({ ...s, ...p }))} />
        <LabFields legend="Campione" lab={smp} set={(p) => setSmp((s) => ({ ...s, ...p }))} />
      </div>
      <div className="mt-3">
        <Button type="button" loading={run.isPending} onClick={() => run.mutate()}>
          Confronta (D65 vs A)
        </Button>
      </div>
      <ErrorText error={run.error} />
      {run.data && <Results data={run.data} />}
    </Card>
  );
}
