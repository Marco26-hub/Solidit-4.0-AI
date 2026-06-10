import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  analyzeCaptureSession,
  createCaptureSession,
  createTestJob,
  generateReport,
  getResults,
  listArticles,
  listBatches,
  listBrandSpecs,
  listCalibrationReferences,
  listStripProfiles,
  listTestJobs,
  listTestMethods,
  submitManualResult,
  uploadCaptureImage,
} from "@/api/quality";
import { MethodSelect } from "@/components/MethodSelect";
import { PhotoInput } from "@/components/PhotoInput";
import { fibersForMethod } from "@/lib/fibers";
import {
  Badge,
  Button,
  Card,
  ErrorText,
  Field,
  PageHeader,
  TextInput,
  statusBadgeKind,
} from "@/components/ui";

type FiberRow = { fiber: string; delta_e: string; gray_scale_grade: string };
type VisionFiber = {
  delta_e: number | null;
  gray_scale_grade: number | null;
  band_confidence?: number | null;
};

export function TestJobsPage() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const jobs = useQuery({
    queryKey: ["jobs", statusFilter],
    queryFn: () => listTestJobs(statusFilter ? { status: statusFilter } : undefined),
  });
  const specs = useQuery({ queryKey: ["brand-specs"], queryFn: listBrandSpecs });
  const methods = useQuery({ queryKey: ["test-methods"], queryFn: listTestMethods });
  const articles = useQuery({ queryKey: ["articles"], queryFn: listArticles });

  // create form
  const [brandId, setBrandId] = useState("");
  const [methodCode, setMethodCode] = useState("");
  const [article, setArticle] = useState("");
  const [lot, setLot] = useState("");
  // production-sample reference (article + variant) for colour-change
  const [articleId, setArticleId] = useState("");
  const [variantId, setVariantId] = useState("");

  const selectedArticle = (articles.data ?? []).find((a) => a.id === articleId);

  const createJob = useMutation({
    mutationFn: () =>
      createTestJob({
        brand_specification_id: brandId || null,
        test_method_code: methodCode || null,
        article_code: article || null,
        lot_code: lot || null,
        article_id: articleId || null,
        article_variant_id: variantId || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      setArticle("");
      setLot("");
      setArticleId("");
      setVariantId("");
    },
  });

  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <PageHeader title="Test Jobs" subtitle="Prove, risultati manuali e report" />

      <Card>
        <div className="mb-3 font-medium">Nuova prova</div>
        <div className="grid gap-3 md:grid-cols-4">
          <Field label="Brand spec">
            <select
              className="w-full rounded border px-2 py-1.5 text-sm"
              value={brandId}
              onChange={(e) => setBrandId(e.target.value)}
            >
              <option value="">—</option>
              {(specs.data ?? []).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.brand_name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Metodo (solidità)">
            <MethodSelect
              methods={methods.data ?? []}
              value={methodCode}
              onChange={setMethodCode}
              emptyLabel="— scegli —"
            />
          </Field>
          <Field label="Articolo (testo)">
            <TextInput value={article} onChange={(e) => setArticle(e.target.value)} />
          </Field>
          <Field label="Lotto">
            <TextInput value={lot} onChange={(e) => setLot(e.target.value)} />
          </Field>
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <Field label="Articolo di produzione (rif. colour-change)">
            <select
              className="w-full rounded border px-2 py-1.5 text-sm"
              value={articleId}
              onChange={(e) => {
                setArticleId(e.target.value);
                setVariantId("");
              }}
            >
              <option value="">—</option>
              {(articles.data ?? []).map((a) => (
                <option key={a.id} value={a.id}>
                  {a.code}
                  {a.name ? ` · ${a.name}` : ""}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Variante (colore/lotto)">
            <select
              className="w-full rounded border px-2 py-1.5 text-sm"
              value={variantId}
              onChange={(e) => setVariantId(e.target.value)}
              disabled={!selectedArticle}
            >
              <option value="">—</option>
              {(selectedArticle?.variants ?? []).map((v) => (
                <option key={v.id} value={v.id}>
                  {v.code}
                  {v.color_name ? ` · ${v.color_name}` : ""}
                  {v.reference_lab ? "" : " (no Lab rif.)"}
                </option>
              ))}
            </select>
          </Field>
        </div>

        <div className="mt-3">
          <Button type="button" disabled={createJob.isPending} onClick={() => createJob.mutate()}>
            {createJob.isPending ? "…" : "Crea prova"}
          </Button>
        </div>
        <ErrorText error={createJob.error} />
      </Card>

      <Card>
        <div className="mb-3 flex items-center justify-between">
          <span className="font-medium">Prove</span>
          <select
            className="rounded border px-2 py-1 text-sm"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">tutti gli stati</option>
            <option value="created">created</option>
            <option value="passed">passed</option>
            <option value="failed">failed</option>
            <option value="completed">completed</option>
          </select>
        </div>
        <ErrorText error={jobs.error} />
        <div className="overflow-x-auto">
        <table className="w-full min-w-[440px] text-sm">
          <thead className="text-left text-steel">
            <tr>
              <th className="py-1">Articolo</th>
              <th>Lotto</th>
              <th>Stato</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {(jobs.data ?? []).map((j) => (
              <tr key={j.id} className="border-t">
                <td className="py-1.5">{j.article_code ?? "—"}</td>
                <td>{j.lot_code ?? "—"}</td>
                <td>
                  <Badge kind={statusBadgeKind(j.status)}>{j.status}</Badge>
                </td>
                <td className="text-right">
                  <Button variant="ghost" onClick={() => setSelected(selected === j.id ? null : j.id)}>
                    {selected === j.id ? "chiudi" : "apri"}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
        {jobs.data?.length === 0 && <p className="py-2 text-steel">Nessuna prova.</p>}
      </Card>

      {selected && (
        <JobPanel
          jobId={selected}
          defaultMethod={methodCode}
          hasVariant={Boolean((jobs.data ?? []).find((j) => j.id === selected)?.article_variant_id)}
        />
      )}
    </div>
  );
}

function JobPanel({
  jobId,
  defaultMethod,
  hasVariant,
}: {
  jobId: string;
  defaultMethod: string;
  hasVariant: boolean;
}) {
  const qc = useQueryClient();
  const methods = useQuery({ queryKey: ["test-methods"], queryFn: listTestMethods });
  const profiles = useQuery({ queryKey: ["strip-profiles"], queryFn: listStripProfiles });
  const results = useQuery({ queryKey: ["results", jobId], queryFn: () => getResults(jobId) });

  const [methodCode, setMethodCode] = useState(defaultMethod);
  const [rows, setRows] = useState<FiberRow[]>([]);
  const [reportNo, setReportNo] = useState<string | null>(null);

  // auto-load the multifibre fibres of the chosen norm (the operator just fills
  // ΔE/grade; "+ fibra" stays for adding extra fibres). Reloads when the method
  // changes; not while data is still loading.
  const methodsReady = !!methods.data;
  const profilesReady = !!profiles.data;
  useEffect(() => {
    if (!methodCode || !methodsReady || !profilesReady) return;
    const fibers = fibersForMethod(methodCode, methods.data ?? [], profiles.data ?? []);
    setRows(fibers.map((f) => ({ fiber: f, delta_e: "", gray_scale_grade: "" })));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [methodCode, methodsReady, profilesReady]);

  const submit = useMutation({
    mutationFn: () => {
      const fibers: Record<string, { delta_e?: number | null; gray_scale_grade?: number | null }> = {};
      for (const r of rows) {
        if (!r.fiber) continue;
        fibers[r.fiber] = {
          delta_e: r.delta_e === "" ? null : Number(r.delta_e),
          gray_scale_grade: r.gray_scale_grade === "" ? null : Number(r.gray_scale_grade),
        };
      }
      return submitManualResult(jobId, { test_method_code: methodCode, fibers });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["results", jobId] });
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const report = useMutation({
    mutationFn: () => generateReport(jobId),
    onSuccess: (r) => {
      setReportNo(r.report_number);
      qc.invalidateQueries({ queryKey: ["reports"] });
    },
  });

  const setRow = (i: number, patch: Partial<FiberRow>) =>
    setRows((rs) => rs.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));

  // ── Vision: foto multifibra post-prova → analisi staining ──────────────────
  const batches = useQuery({ queryKey: ["batches"], queryFn: listBatches });
  const calrefs = useQuery({ queryKey: ["calref"], queryFn: listCalibrationReferences });
  const [visBatch, setVisBatch] = useState("");
  const [visFile, setVisFile] = useState<File | null>(null);
  const [lightboxRef, setLightboxRef] = useState("");
  const [greyRef, setGreyRef] = useState("");
  const refIds = () => ({
    lightbox_ref_id: lightboxRef || null,
    grey_scale_ref_id: greyRef || null,
  });
  const usableRefs = (kind: string) =>
    (calrefs.data ?? []).filter((r) => r.kind === kind && r.validity !== "retired");
  const vision = useMutation({
    mutationFn: async () => {
      const cs = await createCaptureSession({
        test_job_id: jobId,
        batch_id: visBatch,
        test_method_code: methodCode,
        capture_type: "multifiber_after",
        ...refIds(),
      });
      if (visFile) await uploadCaptureImage(cs.id, visFile, "multifiber_after");
      return analyzeCaptureSession(cs.id);
    },
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["results", jobId] });
      qc.invalidateQueries({ queryKey: ["jobs"] });
      setVisFile(null);
      // bridge Vision -> manual: prefill the manual rows with the photo's ΔE/grade
      // so the operator VERIFIES/corrects before generating the report (human-in-the-loop)
      const vf = (res.results as { vision?: { fibers?: Record<string, VisionFiber> } })?.vision
        ?.fibers;
      if (vf) {
        setRows(
          Object.entries(vf).map(([fiber, v]) => ({
            fiber,
            delta_e: v.delta_e != null ? String(v.delta_e) : "",
            gray_scale_grade: v.gray_scale_grade != null ? String(v.gray_scale_grade) : "",
          }))
        );
      }
    },
  });

  // ── Vision: colour-change vs variante di produzione ────────────────────────
  const [ccFile, setCcFile] = useState<File | null>(null);
  const colourChange = useMutation({
    mutationFn: async () => {
      const cs = await createCaptureSession({
        test_job_id: jobId,
        test_method_code: methodCode,
        capture_type: "colour_change",
        ...refIds(),
      });
      if (ccFile) await uploadCaptureImage(cs.id, ccFile, "fabric_after");
      return analyzeCaptureSession(cs.id);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["results", jobId] });
      qc.invalidateQueries({ queryKey: ["jobs"] });
      setCcFile(null);
    },
  });

  return (
    <Card>
      <div className="mb-2 font-medium">Risultato manuale</div>
      <div className="grid gap-2 md:grid-cols-3">
        <Field label="Metodo">
          <MethodSelect
            methods={methods.data ?? []}
            value={methodCode}
            onChange={setMethodCode}
            emptyLabel="—"
          />
        </Field>
      </div>

      <div className="mt-2 space-y-2">
        {rows.map((r, i) => (
          <div key={i} className="grid grid-cols-4 gap-2">
            <TextInput
              placeholder="fibra"
              value={r.fiber}
              onChange={(e) => setRow(i, { fiber: e.target.value })}
            />
            <TextInput
              type="number"
              step="0.01"
              placeholder="ΔE"
              value={r.delta_e}
              onChange={(e) => setRow(i, { delta_e: e.target.value })}
            />
            <TextInput
              type="number"
              step="0.5"
              placeholder="grey scale"
              value={r.gray_scale_grade}
              onChange={(e) => setRow(i, { gray_scale_grade: e.target.value })}
            />
            <Button variant="ghost" onClick={() => setRows((rs) => rs.filter((_, idx) => idx !== i))}>
              ✕
            </Button>
          </div>
        ))}
      </div>
      <div className="mt-3 flex gap-2">
        <Button
          variant="ghost"
          onClick={() => setRows((rs) => [...rs, { fiber: "", delta_e: "", gray_scale_grade: "" }])}
        >
          + fibra
        </Button>
        <Button disabled={!methodCode || submit.isPending} onClick={() => submit.mutate()}>
          {submit.isPending ? "…" : "Salva risultato"}
        </Button>
        <Button variant="ghost" disabled={report.isPending} onClick={() => report.mutate()}>
          {report.isPending ? "…" : "Genera report"}
        </Button>
      </div>
      <ErrorText error={submit.error || report.error} />
      {reportNo && <p className="mt-2 text-sm text-green-700">Report generato: {reportNo} (vedi Ledger)</p>}

      <div className="mt-5 border-t pt-4">
        <div className="mb-2 font-medium">Analisi Vision — foto multifibra (staining)</div>
        <div className="grid gap-2 md:grid-cols-3">
          <Field label="Lotto multifibra (batch)">
            <select
              className="w-full rounded border px-2 py-1.5 text-sm"
              value={visBatch}
              onChange={(e) => setVisBatch(e.target.value)}
            >
              <option value="">—</option>
              {(batches.data ?? []).map((b) => (
                <option key={b.id} value={b.id}>
                  {b.batch_code} {b.strip_profile_code ? `(${b.strip_profile_code})` : ""}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Foto multifibra post-prova">
            <PhotoInput onFile={setVisFile} />
          </Field>
          <div className="flex items-end">
            <Button
              disabled={!visBatch || !visFile || !methodCode || vision.isPending}
              onClick={() => vision.mutate()}
            >
              {vision.isPending ? "…" : "Analizza staining"}
            </Button>
          </div>
        </div>
        <div className="mt-2 grid gap-2 md:grid-cols-2">
          <Field label="Light box (riferimento)">
            <select
              className="w-full rounded border px-2 py-1.5 text-sm"
              value={lightboxRef}
              onChange={(e) => setLightboxRef(e.target.value)}
            >
              <option value="">— nessuno —</option>
              {usableRefs("lightbox").map((r) => (
                <option key={r.id} value={r.id}>
                  {r.code} {r.validity === "expiring" ? "(in scadenza)" : ""}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Scala grigia (riferimento)">
            <select
              className="w-full rounded border px-2 py-1.5 text-sm"
              value={greyRef}
              onChange={(e) => setGreyRef(e.target.value)}
            >
              <option value="">— nessuno —</option>
              {usableRefs("grey_scale").map((r) => (
                <option key={r.id} value={r.id}>
                  {r.code} {r.validity === "expiring" ? "(in scadenza)" : ""}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <p className="mt-1 text-xs text-steel">
          Foto della sola striscia multifibra: le bande vengono riconosciute in ordine secondo la
          norma del lotto. I valori ΔE/grado della foto precompilano i campi di "Risultato manuale"
          sopra — verifica/correggi e poi salva.
        </p>
        <ErrorText error={vision.error} />
      </div>

      <div className="mt-5 border-t pt-4">
        <div className="mb-2 font-medium">Analisi Vision — colour-change (vs variante)</div>
        {hasVariant ? (
          <>
            <div className="grid gap-2 md:grid-cols-3">
              <Field label="Foto tessuto post-prova">
                <PhotoInput onFile={setCcFile} />
              </Field>
              <div className="flex items-end md:col-span-2">
                <Button
                  disabled={!ccFile || !methodCode || colourChange.isPending}
                  onClick={() => colourChange.mutate()}
                >
                  {colourChange.isPending ? "…" : "Analizza colour-change"}
                </Button>
              </div>
            </div>
            <p className="mt-1 text-xs text-steel">
              ΔE del tessuto vs Lab di riferimento della variante → grado di variazione colore
              (norma del metodo).
            </p>
            <ErrorText error={colourChange.error} />
          </>
        ) : (
          <p className="text-sm text-steel">
            Crea la prova selezionando un articolo + variante (con Lab di riferimento) per abilitare
            il colour-change.
          </p>
        )}
      </div>

      <div className="mt-4 text-sm font-medium">Risultati</div>
      {(results.data ?? []).map((res) => {
        const r = res.results as {
          test_method_code?: string;
          source?: string;
          assessment_type?: string;
          vision?: {
            fibers?: Record<string, VisionFiber>;
            delta_e?: number;
            gray_scale_grade?: number;
            warnings?: string[];
            quality_flags?: {
              orientation?: string;
              boundary_method?: string;
              fill_ratio?: number;
            };
          };
          references?: Record<string, { code: string; validity: string }>;
        };
        const visFibers = r?.vision?.fibers;
        const warnings = r?.vision?.warnings ?? [];
        const qf = r?.vision?.quality_flags;
        const refs = r?.references ?? {};
        const isChange = r?.assessment_type === "change";
        return (
          <div key={res.id} className="mt-1 rounded border p-2 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <Badge kind={res.pass_fail.overall_pass ? "pass" : res.pass_fail.evaluated ? "fail" : "warn"}>
                {res.pass_fail.overall_pass ? "PASS" : res.pass_fail.evaluated ? "FAIL" : "inconclusive"}
              </Badge>
              <span className="text-steel">{r?.test_method_code ?? "—"}</span>
              <span className="text-xs text-slate-500">
                {isChange ? "colour-change" : "staining"}
              </span>
              <span className="text-xs text-slate-400">
                {r?.source === "vision" ? "📷 vision" : "✎ manuale"} · {res.algorithm_version}
              </span>
            </div>
            {qf && (
              <div className="mt-1 text-[11px] text-slate-400">
                striscia: {qf.orientation ?? "—"} · bande {qf.boundary_method ?? "—"} · fill{" "}
                {qf.fill_ratio != null ? `${Math.round(qf.fill_ratio * 100)}%` : "—"}
              </div>
            )}
            {Object.keys(refs).length > 0 && (
              <div className="mt-1 text-[11px] text-slate-500">
                riferimenti:{" "}
                {Object.entries(refs)
                  .map(([slot, rr]) => `${slot}=${rr.code} (${rr.validity})`)
                  .join(" · ")}
              </div>
            )}
            {warnings.length > 0 && (
              <div className="mt-1 rounded bg-amber-50 px-2 py-1 text-[11px] text-amber-700">
                ⚠ qualità cattura: {warnings.join(" · ")}
              </div>
            )}
            {visFibers && (
              <div className="mt-1 grid grid-cols-2 gap-x-4 text-xs text-steel sm:grid-cols-3">
                {Object.entries(visFibers).map(([fiber, v]) => (
                  <span key={fiber}>
                    {fiber}: ΔE {v.delta_e} → <b>{v.gray_scale_grade}</b>
                    {v.band_confidence != null && (
                      <span className="text-slate-400"> ({Math.round(v.band_confidence * 100)}%)</span>
                    )}
                  </span>
                ))}
              </div>
            )}
            {isChange && r?.vision?.delta_e !== undefined && (
              <div className="mt-1 text-xs text-steel">
                tessuto vs riferimento: ΔE {r.vision.delta_e} → grado{" "}
                <b>{r.vision.gray_scale_grade}</b>
              </div>
            )}
          </div>
        );
      })}
      {results.data?.length === 0 && <p className="text-steel">Nessun risultato.</p>}
    </Card>
  );
}
