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
import { estimateForResult } from "@/api/spectral";
import { SpectralCurveViewer } from "@/features/spectral/SpectralCurveViewer";
import { MethodSelect } from "@/components/MethodSelect";
import { PhotoInput } from "@/components/PhotoInput";
import { fibersForMethod } from "@/lib/fibers";
import {
  Badge,
  Button,
  Card,
  ErrorText,
  Field,
  Hint,
  PageHeader,
  Select,
  TextInput,
  statusBadgeKind,
} from "@/components/ui";

// DB status enum → Italian display label (value stays for queries/badges)
const JOB_STATUS_IT: Record<string, string> = {
  created: "Creata",
  passed: "Conforme",
  failed: "Non conforme",
  completed: "Completata",
};
const jobStatusLabel = (s: string) => JOB_STATUS_IT[s] ?? s;

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

  const [selected, setSelected] = useState<string | null>(null);

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
    onSuccess: (job) => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      setArticle("");
      setLot("");
      setArticleId("");
      setVariantId("");
      if (job?.id) setSelected(job.id); // open the new test straight away
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Prove" subtitle="Prove, risultati manuali e report" />

      <Card>
        <div className="mb-3 font-medium">Nuova prova</div>
        <div className="grid gap-3 md:grid-cols-4">
          <Field label="Brand spec">
            <Select value={brandId} onChange={(e) => setBrandId(e.target.value)}>
              <option value="">—</option>
              {(specs.data ?? []).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.brand_name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Metodo (solidità)">
            <MethodSelect
              methods={methods.data ?? []}
              value={methodCode}
              onChange={setMethodCode}
              emptyLabel="— scegli —"
            />
          </Field>
          <Field label="Codice articolo (libero)">
            <TextInput value={article} onChange={(e) => setArticle(e.target.value)} placeholder="es. ART-001" />
          </Field>
          <Field label="Lotto">
            <TextInput value={lot} onChange={(e) => setLot(e.target.value)} placeholder="es. L-2026-014" />
          </Field>
        </div>

        <p className="mt-3 text-xs text-steel">
          Articolo a catalogo + variante servono solo per la <b>variazione di colore</b>{" "}
          (colour-change). Per la sola prova di macchia puoi lasciarli vuoti.
        </p>
        <div className="mt-2 grid gap-3 md:grid-cols-2">
          <Field label="Articolo a catalogo (per variazione colore)">
            <Select
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
            </Select>
          </Field>
          <Field label="Variante (colore/lotto)">
            <Select
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
            </Select>
          </Field>
        </div>

        <div className="mt-3">
          <Button
            type="button"
            loading={createJob.isPending}
            disabled={!methodCode}
            onClick={() => createJob.mutate()}
          >
            Crea prova
          </Button>
          {!methodCode && <Hint>Scegli il metodo (norma di solidità) per creare la prova.</Hint>}
        </div>
        <ErrorText error={createJob.error} />
      </Card>

      <Card>
        <div className="mb-3 flex items-center justify-between">
          <span className="font-medium">Prove</span>
          <Select
            className="w-auto"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">Tutti gli stati</option>
            <option value="created">Creata</option>
            <option value="passed">Conforme</option>
            <option value="failed">Non conforme</option>
            <option value="completed">Completata</option>
          </Select>
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
                  <Badge kind={statusBadgeKind(j.status)}>{jobStatusLabel(j.status)}</Badge>
                </td>
                <td className="text-right">
                  <Button
                    variant={selected === j.id ? "ghost" : "primary"}
                    onClick={() => setSelected(selected === j.id ? null : j.id)}
                  >
                    {selected === j.id ? "Chiudi" : "Apri prova ›"}
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
  // true when the rows below were pre-filled by the Vision analysis (so the
  // operator knows to verify/correct rather than that they typed them)
  const [prefilled, setPrefilled] = useState(false);

  // auto-load the multifibre fibres of the chosen norm (the operator just fills
  // ΔE/grade; "+ fibra" stays for adding extra fibres). Reloads when the method
  // changes; not while data is still loading.
  const methodsReady = !!methods.data;
  const profilesReady = !!profiles.data;
  useEffect(() => {
    if (!methodCode || !methodsReady || !profilesReady) return;
    const fibers = fibersForMethod(methodCode, methods.data ?? [], profiles.data ?? []);
    setRows(fibers.map((f) => ({ fiber: f, delta_e: "", gray_scale_grade: "" })));
    setPrefilled(false);
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
  const hasResult = (results.data?.length ?? 0) > 0;

  // ── Vision: foto multifibra post-prova → analisi staining ──────────────────
  const batches = useQuery({ queryKey: ["batches"], queryFn: listBatches });
  const calrefs = useQuery({ queryKey: ["calref"], queryFn: listCalibrationReferences });
  const [visBatch, setVisBatch] = useState("");
  const [visFile, setVisFile] = useState<File | null>(null);
  const [lightboxRef, setLightboxRef] = useState("");
  const [greyRef, setGreyRef] = useState("");
  const [whiteTileRef, setWhiteTileRef] = useState("");
  const [inframeGrey, setInframeGrey] = useState(false);
  const [arucoRectify, setArucoRectify] = useState(false);
  const [strict, setStrict] = useState(false);
  const refIds = () => ({
    lightbox_ref_id: lightboxRef || null,
    grey_scale_ref_id: greyRef || null,
    white_tile_ref_id: whiteTileRef || null,
    has_inframe_grey_scale: inframeGrey,
    aruco_rectify: arucoRectify,
    strict_quality: strict,
  });
  const usableRefs = (kind: string) =>
    (calrefs.data ?? []).filter((r) => r.kind === kind && r.validity !== "retired");
  const stainingHardwareReady = Boolean(lightboxRef && greyRef && whiteTileRef);
  const colourChangeHardwareReady = Boolean(lightboxRef && whiteTileRef);
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
        setPrefilled(true);
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
      <div className="mb-1 flex flex-wrap items-center gap-2">
        <span className="font-medium">Risultato della prova</span>
        {prefilled && <Badge kind="warn">precompilato da Vision — verifica</Badge>}
      </div>
      <div className="mb-3 rounded-lg bg-slate-50 p-2 text-xs leading-relaxed text-steel">
        È la valutazione che finisce nel <b>report</b>. Per ogni fibra inserisci{" "}
        <b>ΔE</b> (differenza di colore misurata) e il <b>grado scala grigi</b> (5 = nessuna
        variazione/macchia → 1 = forte). Puoi compilarlo a mano oppure lasciare che l'
        <b>Analisi Vision</b> qui sotto lo precompili dalla foto: in quel caso{" "}
        <b>verifica/correggi</b> i valori e poi <b>Salva risultato</b>. <b>Genera report</b>{" "}
        produce il PDF con sigillo.
      </div>
      <div className="grid gap-2 md:grid-cols-3">
        <Field label="Metodo (norma di solidità)">
          <MethodSelect
            methods={methods.data ?? []}
            value={methodCode}
            onChange={setMethodCode}
            emptyLabel="—"
          />
        </Field>
      </div>

      {rows.length > 0 && (
        <div className="mt-3 hidden items-center gap-2 px-1 text-[11px] font-medium uppercase tracking-wide text-steel sm:flex">
          <span className="flex-1">Fibra</span>
          <span className="flex-1">ΔE</span>
          <span className="flex-1">Grado scala grigi</span>
          <span className="w-12 shrink-0" />
        </div>
      )}
      <div className="mt-2 space-y-2">
        {rows.map((r, i) => (
          <div key={i} className="flex flex-wrap items-center gap-2">
            <TextInput
              placeholder="fibra"
              className="basis-full sm:flex-1 sm:basis-0"
              value={r.fiber}
              onChange={(e) => setRow(i, { fiber: e.target.value })}
            />
            <TextInput
              type="number"
              inputMode="decimal"
              step="0.01"
              placeholder="ΔE"
              className="min-w-0 flex-1"
              value={r.delta_e}
              onChange={(e) => setRow(i, { delta_e: e.target.value })}
            />
            <TextInput
              type="number"
              inputMode="decimal"
              step="0.5"
              placeholder="grado"
              className="min-w-0 flex-1"
              value={r.gray_scale_grade}
              onChange={(e) => setRow(i, { gray_scale_grade: e.target.value })}
            />
            <Button
              variant="ghost"
              className="shrink-0 px-3"
              aria-label="rimuovi fibra"
              onClick={() => setRows((rs) => rs.filter((_, idx) => idx !== i))}
            >
              ✕
            </Button>
          </div>
        ))}
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          variant="ghost"
          onClick={() => setRows((rs) => [...rs, { fiber: "", delta_e: "", gray_scale_grade: "" }])}
        >
          + fibra
        </Button>
        <Button loading={submit.isPending} disabled={!methodCode} onClick={() => submit.mutate()}>
          Salva risultato
        </Button>
        <Button
          variant={hasResult ? "primary" : "ghost"}
          loading={report.isPending}
          disabled={!hasResult}
          onClick={() => report.mutate()}
        >
          Genera report
        </Button>
      </div>
      {!hasResult && <Hint>Salva prima un risultato per poter generare il report.</Hint>}
      {submit.isSuccess && hasResult && !reportNo && (
        <p className="mt-2 text-xs text-emerald-700">Risultato salvato — ora puoi Generare report.</p>
      )}
      <ErrorText error={submit.error || report.error} />
      {reportNo && (
        <p className="mt-2 text-sm text-green-700">
          Report generato: {reportNo} — lo trovi in <b>Report</b> (verifica, finalizza, scarica PDF).
        </p>
      )}

      <div className="mt-5 border-t pt-4">
        <div className="mb-2 font-medium">Analisi Vision — macchia su multifibra (staining)</div>
        <p className="mb-2 text-xs text-steel">
          Scatta la foto della striscia multifibra dopo la prova: l'app misura quanto colore si è
          trasferito su ogni fibra e precompila i campi del risultato sopra.
        </p>
        <div className="grid gap-2 md:grid-cols-3">
          <Field label="Lotto multifibra">
            <Select value={visBatch} onChange={(e) => setVisBatch(e.target.value)}>
              <option value="">—</option>
              {(batches.data ?? []).map((b) => (
                <option key={b.id} value={b.id}>
                  {b.batch_code} {b.strip_profile_code ? `(${b.strip_profile_code})` : ""}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Foto multifibra post-prova">
            <PhotoInput onFile={setVisFile} />
          </Field>
          <div className="flex items-end">
            <Button
              loading={vision.isPending}
              disabled={!visBatch || !visFile || !methodCode || !stainingHardwareReady}
              onClick={() => vision.mutate()}
            >
              Analizza macchia
            </Button>
          </div>
        </div>
        <div className="mt-2 grid gap-2 md:grid-cols-3">
          <Field label="Light box (riferimento)">
            <Select value={lightboxRef} onChange={(e) => setLightboxRef(e.target.value)}>
              <option value="">— nessuno —</option>
              {usableRefs("lightbox").map((r) => (
                <option key={r.id} value={r.id}>
                  {r.code} {r.validity === "expiring" ? "(in scadenza)" : ""}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Scala grigia (riferimento)">
            <Select value={greyRef} onChange={(e) => setGreyRef(e.target.value)}>
              <option value="">— nessuno —</option>
              {usableRefs("grey_scale").map((r) => (
                <option key={r.id} value={r.id}>
                  {r.code} {r.validity === "expiring" ? "(in scadenza)" : ""}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Piastrina bianca certificata">
            <Select value={whiteTileRef} onChange={(e) => setWhiteTileRef(e.target.value)}>
              <option value="">— nessuna —</option>
              {usableRefs("white_tile").map((r) => (
                <option key={r.id} value={r.id}>
                  {r.code} {r.validity === "expiring" ? "(in scadenza)" : ""}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        {!stainingHardwareReady && (
          <Hint>
            Analisi Vision bloccata: seleziona light box, scala grigia e piastrina bianca validi.
          </Hint>
        )}
        <div className="mt-2 flex flex-wrap gap-4">
          <label className="flex items-center gap-2 text-sm text-steel">
            <input
              type="checkbox"
              checked={inframeGrey}
              onChange={(e) => setInframeGrey(e.target.checked)}
            />
            La foto include una scala grigi/piastrina per la correzione colore (ISO 105-A11)
          </label>
          <label className="flex items-center gap-2 text-sm text-steel">
            <input
              type="checkbox"
              checked={arucoRectify}
              onChange={(e) => setArucoRectify(e.target.checked)}
            />
            La dima ha i 4 marker ArUco: raddrizza la prospettiva (omografia)
          </label>
          <label className="flex items-center gap-2 text-sm text-steel">
            <input type="checkbox" checked={strict} onChange={(e) => setStrict(e.target.checked)} />
            Modalità severa: rifiuta foto di qualità insufficiente
          </label>
        </div>
        <p className="mt-1 text-xs text-steel">
          Inquadra la sola striscia multifibra: le bande vengono riconosciute in ordine secondo la
          norma del lotto. I valori ΔE/grado precompilano il <b>Risultato della prova</b> sopra —
          verifica/correggi e poi salva.
        </p>
        <ErrorText error={vision.error} />
      </div>

      <div className="mt-5 border-t pt-4">
        <div className="mb-2 font-medium">Analisi Vision — variazione di colore (colour-change)</div>
        {hasVariant ? (
          <>
            <p className="mb-2 text-xs text-steel">
              Confronta il tessuto dopo la prova con il colore di riferimento della variante: misura
              quanto il campione stesso ha cambiato colore.
            </p>
            <div className="grid gap-2 md:grid-cols-3">
              <Field label="Foto tessuto post-prova">
                <PhotoInput onFile={setCcFile} />
              </Field>
              <div className="flex items-end md:col-span-2">
                <Button
                  loading={colourChange.isPending}
                  disabled={!ccFile || !methodCode || !colourChangeHardwareReady}
                  onClick={() => colourChange.mutate()}
                >
                  Analizza variazione
                </Button>
              </div>
            </div>
            {!colourChangeHardwareReady && (
              <Hint>
                Colour-change bloccato: seleziona light box e piastrina bianca validi nella sezione
                Vision.
              </Hint>
            )}
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
              colour_correction?: string;
              grey_scale?: { detected?: boolean };
            };
            repeatability?: { replicates?: number; max_deviation_grade?: number };
          };
          references?: Record<string, { code: string; validity: string }>;
        };
        const visFibers = r?.vision?.fibers;
        const warnings = r?.vision?.warnings ?? [];
        const qf = r?.vision?.quality_flags;
        const rep = r?.vision?.repeatability;
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
                {qf.fill_ratio != null ? `${Math.round(qf.fill_ratio * 100)}%` : "—"} · corr.
                colore {qf.colour_correction ?? "—"}
                {qf.grey_scale?.detected ? " (grey-scale ✓)" : ""}
                {rep && rep.replicates != null
                  ? ` · ${rep.replicates} repliche, scarto ${rep.max_deviation_grade}`
                  : ""}
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
            <SpectralResultPanel resultId={res.id} />
          </div>
        );
      })}
      {results.data?.length === 0 && <p className="text-steel">Nessun risultato.</p>}
    </Card>
  );
}

// Per-result reflectance ESTIMATE (R&D). It is NOT a measurement and is
// excluded from the sealed report (project rule 7) — surfaced on demand only.
function SpectralResultPanel({ resultId }: { resultId: string }) {
  const [open, setOpen] = useState(false);
  const estimate = useMutation({
    mutationFn: () => estimateForResult(resultId),
  });

  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next && !estimate.data && !estimate.isPending) estimate.mutate();
  };

  const data = estimate.data;

  return (
    <div className="mt-2 border-t pt-2">
      <Button variant="ghost" loading={estimate.isPending && open} onClick={toggle}>
        {open ? "Nascondi curva riflettanza" : "Curva riflettanza STIMATA (R&D)"}
      </Button>
      {open && (
        <div className="mt-2 space-y-3">
          <ErrorText error={estimate.error} />
          {data && (
            <>
              <div className="rounded-lg border border-amber-300 bg-amber-50 p-2 text-[11px] leading-relaxed text-amber-800">
                <b>{data.label}</b> — {data.disclaimer}
                {data.note ? <span> {data.note}</span> : null}
              </div>
              {data.fibers.length === 0 && (
                <p className="text-xs text-steel">Nessuna fibra con Lab disponibile per la stima.</p>
              )}
              {data.fibers.map((f) => (
                <SpectralCurveViewer key={f.fiber} estimate={f.estimate} title={f.fiber} />
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}
