import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import {
  characterizeCamera,
  computeUncertainty,
  DEGREES,
  type CharacterizationResult,
  type PolynomialDegree,
  type UncertaintyResult,
} from "@/api/colorimetry";
import {
  Badge,
  Button,
  Card,
  ErrorText,
  Field,
  PageHeader,
  Select,
  Stat,
  TextInput,
} from "@/components/ui";

// Demo 24-patch LINEAR camera dataset (ColorChecker-style). LINEAR RGB, 0..1.
const COLORCHECKER_DEMO: number[][] = [
  [0.1944, 0.0878, 0.0581],
  [0.6264, 0.3078, 0.2271],
  [0.11, 0.2043, 0.3241],
  [0.131, 0.1537, 0.0598],
  [0.2382, 0.2383, 0.4196],
  [0.1589, 0.5167, 0.4229],
  [0.8336, 0.2358, 0.055],
  [0.0434, 0.1201, 0.3727],
  [0.6079, 0.1125, 0.1232],
  [0.1119, 0.0531, 0.1348],
  [0.4257, 0.5001, 0.0794],
  [0.8833, 0.3872, 0.057],
  [0.0096, 0.0614, 0.271],
  [0.085, 0.2876, 0.0782],
  [0.4849, 0.0605, 0.0486],
  [0.9912, 0.5993, 0.0579],
  [0.5512, 0.1169, 0.2868],
  [0.025, 0.2456, 0.3712],
  [1.0, 0.9425, 0.8601],
  [0.6637, 0.6317, 0.6001],
  [0.4062, 0.3915, 0.3747],
  [0.2157, 0.2038, 0.1948],
  [0.0975, 0.0947, 0.092],
  [0.0355, 0.0337, 0.0331],
];

// Editable cells are strings so the user can type freely; we parse on submit.
type Row = [string, string, string];

const toRow = (rgb: number[]): Row => [String(rgb[0] ?? ""), String(rgb[1] ?? ""), String(rgb[2] ?? "")];
const demoRows = (): Row[] => COLORCHECKER_DEMO.map(toRow);

function fmt(n: number, digits = 2): string {
  return Number.isFinite(n) ? n.toFixed(digits) : "—";
}

/** Tone the residual ΔE into a Stat colour: small = good, large = warn. */
function deltaTone(value: number): "emerald" | "amber" | "slate" {
  if (!Number.isFinite(value)) return "slate";
  if (value <= 1) return "emerald";
  if (value <= 2.5) return "amber";
  return "slate";
}

export function ColorimetryPage() {
  const [rows, setRows] = useState<Row[]>(demoRows);
  const [degree, setDegree] = useState<PolynomialDegree>(3);

  // Uncertainty budget inputs (all ΔE units, optional). Kept as strings.
  const [repeatability, setRepeatability] = useState("");
  const [characterisation, setCharacterisation] = useState("");
  const [reproducibility, setReproducibility] = useState("");
  const [reference, setReference] = useState("");
  const [coverageFactor, setCoverageFactor] = useState("2");

  const characterize = useMutation<CharacterizationResult>({
    mutationFn: () => {
      const patches = rows
        .map((row) => row.map((c) => Number(c)))
        .filter((p) => p.length === 3 && p.every((v) => Number.isFinite(v)));
      return characterizeCamera({ patches, degree });
    },
    onSuccess: (data) => {
      // Auto-prefill the characterisation uncertainty with the fit's RMS ΔE.
      setCharacterisation(fmt(data.residual.rms_delta_e, 3));
    },
  });

  const uncertainty = useMutation<UncertaintyResult>({
    mutationFn: () => {
      const num = (s: string): number | undefined => {
        const v = Number(s);
        return s.trim() !== "" && Number.isFinite(v) ? v : undefined;
      };
      return computeUncertainty({
        repeatability: num(repeatability),
        characterisation: num(characterisation),
        reproducibility: num(reproducibility),
        reference: num(reference),
        coverage_factor: num(coverageFactor),
      });
    },
  });

  const validRowCount = useMemo(
    () =>
      rows.filter(
        (row) => row.length === 3 && row.every((c) => c.trim() !== "" && Number.isFinite(Number(c)))
      ).length,
    [rows]
  );
  const canCharacterize = validRowCount >= 6 && validRowCount <= 140;

  function updateCell(rowIdx: number, colIdx: number, value: string) {
    setRows((prev) =>
      prev.map((row, i) => {
        if (i !== rowIdx) return row;
        const next = [...row] as Row;
        next[colIdx] = value;
        return next;
      })
    );
  }

  function addRow() {
    setRows((prev) => [...prev, ["", "", ""]]);
  }

  function removeRow(rowIdx: number) {
    setRows((prev) => prev.filter((_, i) => i !== rowIdx));
  }

  const fit = characterize.data;
  const maxResidual = useMemo(() => {
    if (!fit || fit.per_patch.length === 0) return 0;
    return Math.max(...fit.per_patch.map((p) => p.delta_e), 0.0001);
  }, [fit]);

  const unc = uncertainty.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Colorimetria (caratterizzazione + incertezza)"
        subtitle="Colore di livello colorimetro via caratterizzazione della camera — non uno spettrofotometro"
      />

      {/* Honesty intro */}
      <Card>
        <p className="text-sm leading-relaxed text-steel">
          Questo strumento porta la camera a un colore di <b>livello colorimetro</b> tramite una{" "}
          <b>caratterizzazione</b> su patch di riferimento. <b>Non</b> è uno spettrofotometro e{" "}
          <b>non</b> è una ricostruzione spettrale. Dopo la caratterizzazione la camera{" "}
          <b>eguaglia un colorimetro</b> su campioni <b>opachi</b>, sotto l'<b>illuminante di
          ripresa</b>, entro un ΔE validato. <b>Non</b> copre il metamerismo multi-illuminante, gli
          sbiancanti ottici / UV, né i colori con effetto o brillantezza (gloss).
        </p>
        <p className="mt-2 text-sm leading-relaxed text-steel">
          L'RGB in ingresso deve essere <b>RGB lineare della camera</b> (RAW / ProRAW linearizzato),{" "}
          <b>non</b> sRGB con gamma. Valori ammessi 0–1 oppure 0–255.
        </p>
      </Card>

      {/* ── Caratterizzazione camera ─────────────────────────────────────────── */}
      <Card>
        <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold text-ink">Caratterizzazione camera</h2>
            <p className="mt-0.5 text-xs text-steel">
              Inserisci le patch in <b>RGB lineare</b> (RAW/ProRAW), una riga per patch [R G B]. Servono
              da 6 a 140 righe.
            </p>
          </div>
          <Badge kind="muted">{validRowCount} patch valide</Badge>
        </div>

        <div className="mb-3 flex flex-wrap items-center gap-2">
          <Button variant="ghost" type="button" onClick={() => setRows(demoRows())}>
            Carica esempio ColorChecker
          </Button>
          <Button variant="ghost" type="button" onClick={addRow}>
            Aggiungi riga
          </Button>
        </div>

        {/* editable patch grid */}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[360px] border-collapse text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-steel">
                <th className="w-8 py-1 pr-2 font-medium">#</th>
                <th className="py-1 pr-2 font-medium">R lin</th>
                <th className="py-1 pr-2 font-medium">G lin</th>
                <th className="py-1 pr-2 font-medium">B lin</th>
                <th className="w-10 py-1 font-medium" />
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="py-1 pr-2 text-xs text-steel">{i + 1}</td>
                  {[0, 1, 2].map((col) => (
                    <td key={col} className="py-1 pr-2">
                      <TextInput
                        type="number"
                        step="0.0001"
                        inputMode="decimal"
                        aria-label={`patch ${i + 1} canale ${["R", "G", "B"][col]}`}
                        value={row[col]}
                        onChange={(e) => updateCell(i, col, e.target.value)}
                      />
                    </td>
                  ))}
                  <td className="py-1">
                    <Button
                      variant="ghost"
                      type="button"
                      aria-label={`rimuovi riga ${i + 1}`}
                      className="px-2"
                      onClick={() => removeRow(i)}
                    >
                      Rimuovi
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex flex-wrap items-end gap-3">
          <Field label="Grado polinomiale" hint="Default 3 — più alto = adattamento più flessibile.">
            <Select
              value={degree}
              onChange={(e) => setDegree(Number(e.target.value) as PolynomialDegree)}
            >
              {DEGREES.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </Select>
          </Field>
          <Button
            type="button"
            loading={characterize.isPending}
            disabled={!canCharacterize}
            onClick={() => characterize.mutate()}
          >
            Caratterizza
          </Button>
        </div>
        {!canCharacterize && (
          <p className="mt-2 text-xs text-steel">Servono da 6 a 140 patch valide per caratterizzare.</p>
        )}
        <ErrorText error={characterize.error} />

        {fit && (
          <div className="mt-5 space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-ink">Budget ΔE residuo</span>
              <Badge kind="muted">{fit.method}</Badge>
              <Badge kind="muted">grado {fit.degree}</Badge>
              <Badge kind="muted">{fit.n_terms} termini</Badge>
              <Badge kind="muted">{fit.n_patches} patch</Badge>
              <span className="text-xs text-steel">rif. {fit.reference}</span>
            </div>

            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <Stat
                label="ΔE medio"
                value={fmt(fit.residual.mean_delta_e)}
                tone={deltaTone(fit.residual.mean_delta_e)}
              />
              <Stat
                label="ΔE max"
                value={fmt(fit.residual.max_delta_e)}
                tone={deltaTone(fit.residual.max_delta_e)}
              />
              <Stat
                label="ΔE RMS"
                value={fmt(fit.residual.rms_delta_e)}
                tone={deltaTone(fit.residual.rms_delta_e)}
              />
              <Stat
                label="ΔE p95"
                value={fmt(fit.residual.p95_delta_e)}
                tone={deltaTone(fit.residual.p95_delta_e)}
              />
            </div>

            {/* per-patch ΔE inline bars */}
            <div>
              <div className="mb-2 text-xs font-medium uppercase tracking-wide text-steel">
                ΔE per patch
              </div>
              <div className="space-y-1">
                {fit.per_patch.map((p) => (
                  <div key={p.patch} className="flex items-center gap-2 text-xs">
                    <span className="w-8 shrink-0 text-right text-steel">#{p.patch}</span>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-brand-500"
                        style={{ width: `${Math.min((p.delta_e / maxResidual) * 100, 100)}%` }}
                      />
                    </div>
                    <span className="w-12 shrink-0 text-right font-medium text-ink">
                      {fmt(p.delta_e)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* fitted matrix */}
            <details className="rounded-lg border border-slate-200 bg-slate-50/60 p-3">
              <summary className="cursor-pointer text-sm font-medium text-steel">
                Matrice di trasformazione ({fit.matrix.length}×{fit.matrix[0]?.length ?? 0})
              </summary>
              <div className="mt-3 overflow-x-auto">
                <table className="border-collapse text-[11px] tabular-nums">
                  <tbody>
                    {fit.matrix.map((mrow, ri) => (
                      <tr key={ri}>
                        {mrow.map((v, ci) => (
                          <td key={ci} className="border border-slate-200 px-2 py-1 text-right text-steel">
                            {fmt(v, 5)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          </div>
        )}
      </Card>

      {/* ── Budget incertezza ────────────────────────────────────────────────── */}
      <Card>
        <h2 className="text-base font-semibold text-ink">Budget incertezza (ISO 17025, semplificato)</h2>
        <p className="mt-0.5 text-xs text-steel">
          Componenti in unità ΔE (tutte facoltative). La componente di caratterizzazione viene
          precompilata con l'RMS del fit dopo una caratterizzazione.
        </p>

        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <Field label="Ripetibilità (ΔE)" hint="Dispersione su ripetizioni nelle stesse condizioni.">
            <TextInput
              type="number"
              step="0.001"
              inputMode="decimal"
              value={repeatability}
              onChange={(e) => setRepeatability(e.target.value)}
            />
          </Field>
          <Field label="Caratterizzazione (ΔE)" hint="Auto: RMS ΔE del fit di caratterizzazione.">
            <TextInput
              type="number"
              step="0.001"
              inputMode="decimal"
              value={characterisation}
              onChange={(e) => setCharacterisation(e.target.value)}
            />
          </Field>
          <Field label="Riproducibilità (ΔE)" hint="Dispersione fra operatori / sessioni / device.">
            <TextInput
              type="number"
              step="0.001"
              inputMode="decimal"
              value={reproducibility}
              onChange={(e) => setReproducibility(e.target.value)}
            />
          </Field>
          <Field label="Riferimento (ΔE)" hint="Incertezza dichiarata dello standard di riferimento.">
            <TextInput
              type="number"
              step="0.001"
              inputMode="decimal"
              value={reference}
              onChange={(e) => setReference(e.target.value)}
            />
          </Field>
          <Field label="Fattore di copertura k" hint="Default 2 (≈ 95%).">
            <TextInput
              type="number"
              step="0.1"
              inputMode="decimal"
              value={coverageFactor}
              onChange={(e) => setCoverageFactor(e.target.value)}
            />
          </Field>
        </div>

        <div className="mt-4">
          <Button type="button" loading={uncertainty.isPending} onClick={() => uncertainty.mutate()}>
            Calcola incertezza
          </Button>
        </div>
        <ErrorText error={uncertainty.error} />

        {unc && (
          <div className="mt-5 space-y-4">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              <Stat
                label="u_c combinata"
                value={fmt(unc.combined_standard_uncertainty)}
                hint={unc.unit}
                tone="brand"
              />
              <Stat label="Fattore k" value={fmt(unc.coverage_factor, 1)} tone="slate" />
              <Stat
                label="U estesa"
                value={fmt(unc.expanded_uncertainty)}
                hint={unc.confidence_level ?? unc.unit}
                tone="amber"
              />
              <Stat
                label="ν effettivi"
                value={unc.effective_degrees_freedom == null ? "∞" : fmt(unc.effective_degrees_freedom, 1)}
                hint={unc.coverage_method}
                tone="slate"
              />
              <Stat
                label="Dominante"
                value={unc.dominant_component ?? "—"}
                hint="quota varianza maggiore"
                tone="slate"
              />
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[360px] border-collapse text-sm">
                <thead>
                  <tr className="text-left text-[11px] uppercase tracking-wide text-steel">
                    <th className="py-1 pr-2 font-medium">Componente</th>
                    <th className="py-1 pr-2 font-medium">u ({unc.unit})</th>
                    <th className="py-1 pr-2 font-medium">Fonte</th>
                    <th className="py-1 font-medium">Quota varianza</th>
                  </tr>
                </thead>
                <tbody>
                  {unc.components.map((c) => (
                    <tr key={c.component} className="border-t border-slate-100">
                      <td className="py-1.5 pr-2 text-ink">{c.component}</td>
                      <td className="py-1.5 pr-2 tabular-nums text-steel">
                        {fmt(c.standard_uncertainty, 3)}
                      </td>
                      <td className="py-1.5 pr-2 text-xs text-steel">
                        {c.source ?? "—"}
                        {c.degrees_freedom != null ? ` · ν=${fmt(c.degrees_freedom, 1)}` : ""}
                      </td>
                      <td className="py-1.5">
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-100">
                            <div
                              className="h-full rounded-full bg-brand-500"
                              style={{ width: `${Math.min(Math.max(c.variance_share_pct, 0), 100)}%` }}
                            />
                          </div>
                          <span className="w-12 shrink-0 text-right tabular-nums text-steel">
                            {fmt(c.variance_share_pct, 1)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {unc.note && (
              <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-xs leading-relaxed text-amber-800">
                {unc.note}
              </div>
            )}
            {unc.decision_rule && (
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-steel">
                Regola decisionale: {unc.decision_rule.verdict} · valore{" "}
                {fmt(unc.decision_rule.measured_value, 3)} · limite{" "}
                {fmt(unc.decision_rule.tolerance_limit, 3)} · guard band{" "}
                {fmt(unc.decision_rule.guard_band, 3)}
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
