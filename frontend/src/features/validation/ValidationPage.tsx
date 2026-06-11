import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addValidationSample,
  computeValidationRun,
  createValidationRun,
  downloadValidationReport,
  getAccreditationReadiness,
  getValidationRun,
  listValidationRuns,
} from "@/api/quality";
import { Badge, Button, Card, EmptyState, ErrorText, Field, PageHeader, TextInput } from "@/components/ui";

export function ValidationPage() {
  const qc = useQueryClient();
  const runs = useQuery({ queryKey: ["validation-runs"], queryFn: listValidationRuns });
  const [name, setName] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);

  const readiness = useQuery({ queryKey: ["readiness"], queryFn: getAccreditationReadiness });

  const create = useMutation({
    mutationFn: () => createValidationRun(name),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["validation-runs"] });
      qc.invalidateQueries({ queryKey: ["readiness"] });
      setName("");
    },
  });

  const statusBadge = (s: string) =>
    s === "done" ? ("pass" as const) : s === "partial" ? ("warn" as const) : ("muted" as const);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Validazione metodo"
        subtitle="Campagne di confronto del software vs riferimento (spettrofotometro / valutazione esperta / laboratorio esterno). È il documento di credibilità per l'accreditamento ISO/IEC 17025."
      />

      {readiness.data && (
        <Card>
          <div className="mb-1 flex items-center justify-between">
            <span className="font-medium">Stato verso l'accreditamento</span>
            <Badge kind="warn">{readiness.data.level}</Badge>
          </div>
          <div className="mb-2 text-xs text-steel">
            {readiness.data.done}/{readiness.data.total} requisiti soddisfatti. L'accreditamento è
            concesso da Accredia (lab + consulente + scopo), non dal software.
          </div>
          <div className="space-y-1">
            {readiness.data.items.map((it) => (
              <div key={it.key} className="flex items-center justify-between gap-2 text-sm">
                <span>{it.label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-steel">{it.detail}</span>
                  <Badge kind={statusBadge(it.status)}>
                    {it.status === "done" ? "ok" : it.status === "partial" ? "parziale" : "manca"}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <div className="mb-3 font-medium">Nuova campagna</div>
        <div className="flex flex-wrap items-end gap-2">
          <Field label="Nome campagna">
            <TextInput
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Pilota 30 campioni"
            />
          </Field>
          <Button type="button" disabled={!name || create.isPending} onClick={() => create.mutate()}>
            {create.isPending ? "…" : "Crea"}
          </Button>
        </div>
        <ErrorText error={create.error} />
      </Card>

      <Card>
        <div className="mb-2 font-medium">Campagne</div>
        <ErrorText error={runs.error} />
        <div className="space-y-3">
          {(runs.data ?? []).map((r) => {
            const m = r.metrics ?? {};
            const pct = m["pct_within_half_grade"];
            const pass = m["indicative_pass"];
            return (
              <div key={r.id} className="rounded-lg border border-slate-200">
                <button
                  type="button"
                  className="flex w-full items-center justify-between px-3 py-2 text-left"
                  onClick={() => setOpenId(openId === r.id ? null : r.id)}
                >
                  <div>
                    <div className="font-medium">{r.name ?? "—"}</div>
                    <div className="text-xs text-steel">
                      {r.status === "computed" && pct != null
                        ? `${pct}% entro ±0.5 grado · scarto medio ${m["mean_abs_grade_dev"]} · RMSE ${m["rmse"]}`
                        : "non ancora calcolata"}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {r.status === "computed" ? (
                      <Badge kind={pass ? "pass" : "fail"}>
                        {pass ? "pass indicativo" : "sotto soglia"}
                      </Badge>
                    ) : (
                      <Badge kind="muted">{r.status}</Badge>
                    )}
                    <span className="text-xs text-steel">{openId === r.id ? "chiudi" : "apri"}</span>
                  </div>
                </button>
                {openId === r.id && <RunDetail runId={r.id} />}
              </div>
            );
          })}
          {runs.data?.length === 0 && (
            <EmptyState
              title="Nessuna campagna"
              hint="Crea una campagna e aggiungi i campioni col grado software vs riferimento."
            />
          )}
        </div>
      </Card>
    </div>
  );
}

function RunDetail({ runId }: { runId: string }) {
  const qc = useQueryClient();
  const detail = useQuery({
    queryKey: ["validation-run", runId],
    queryFn: () => getValidationRun(runId),
  });

  const [code, setCode] = useState("");
  const [fiber, setFiber] = useState("");
  const [method, setMethod] = useState("spectrophotometer");
  const [sw, setSw] = useState("");
  const [ref, setRef] = useState("");

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["validation-run", runId] });
    qc.invalidateQueries({ queryKey: ["validation-runs"] });
  };

  const add = useMutation({
    mutationFn: () =>
      addValidationSample(runId, {
        sample_code: code,
        fiber: fiber || null,
        reference_method: method,
        software_grade: sw === "" ? null : Number(sw),
        reference_grade: ref === "" ? null : Number(ref),
      }),
    onSuccess: () => {
      invalidate();
      setCode("");
      setFiber("");
      setSw("");
      setRef("");
    },
  });

  const compute = useMutation({
    mutationFn: () => computeValidationRun(runId),
    onSuccess: invalidate,
  });

  const samples = detail.data?.samples ?? [];
  const m = detail.data?.metrics ?? {};

  return (
    <div className="border-t px-3 py-3">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[460px] text-sm">
          <thead className="text-left text-steel">
            <tr>
              <th className="py-1">Campione</th>
              <th>Fibra</th>
              <th>Rif.</th>
              <th>Software</th>
              <th>Riferimento</th>
              <th>|scarto|</th>
            </tr>
          </thead>
          <tbody>
            {samples.map((s) => {
              const dev =
                s.software_grade != null && s.reference_grade != null
                  ? Math.abs(s.software_grade - s.reference_grade)
                  : null;
              return (
                <tr key={s.id} className="border-t">
                  <td className="py-1.5">{s.sample_code}</td>
                  <td>{s.fiber ?? "—"}</td>
                  <td className="text-xs text-steel">{s.reference_method}</td>
                  <td>{s.software_grade ?? "—"}</td>
                  <td>{s.reference_grade ?? "—"}</td>
                  <td className={dev != null && dev > 0.5 ? "text-red-600" : ""}>
                    {dev != null ? dev.toFixed(1) : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {samples.length === 0 && <p className="py-2 text-sm text-steel">Nessun campione.</p>}

      <div className="mt-3 grid gap-2 md:grid-cols-6">
        <TextInput placeholder="codice" value={code} onChange={(e) => setCode(e.target.value)} />
        <TextInput placeholder="fibra" value={fiber} onChange={(e) => setFiber(e.target.value)} />
        <select
          className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
          value={method}
          onChange={(e) => setMethod(e.target.value)}
        >
          <option value="spectrophotometer">spettrofotometro</option>
          <option value="visual">visivo esperto</option>
          <option value="external_lab">lab esterno</option>
        </select>
        <TextInput
          type="number"
          step="0.5"
          placeholder="grado SW"
          value={sw}
          onChange={(e) => setSw(e.target.value)}
        />
        <TextInput
          type="number"
          step="0.5"
          placeholder="grado rif."
          value={ref}
          onChange={(e) => setRef(e.target.value)}
        />
        <Button disabled={!code || add.isPending} onClick={() => add.mutate()}>
          {add.isPending ? "…" : "+ campione"}
        </Button>
      </div>
      <ErrorText error={add.error} />

      <div className="mt-3 flex flex-wrap items-center gap-3">
        <Button variant="ghost" disabled={compute.isPending} onClick={() => compute.mutate()}>
          {compute.isPending ? "…" : "Calcola statistiche"}
        </Button>
        {detail.data?.status === "computed" && (
          <Button
            variant="ghost"
            onClick={async () => {
              const blob = await downloadValidationReport(runId);
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `validazione-${runId}.pdf`;
              a.click();
              URL.revokeObjectURL(url);
            }}
          >
            Scarica report PDF
          </Button>
        )}
        {detail.data?.status === "computed" && (
          <div className="text-xs text-steel">
            n={m["scored"]} · {m["pct_within_half_grade"]}% entro ±0.5 · scarto medio{" "}
            {m["mean_abs_grade_dev"]} · bias {m["bias"]} · RMSE {m["rmse"]} · max{" "}
            {m["max_abs_grade_dev"]}
          </div>
        )}
      </div>
      <ErrorText error={compute.error} />
    </div>
  );
}
