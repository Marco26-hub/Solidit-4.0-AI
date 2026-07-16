import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import {
  listBatches,
  listBrandSpecs,
  listCalibrationReferences,
  listMethodDocuments,
  listReports,
  listTestJobs,
} from "@/api/quality";
import { Button, Card } from "@/components/ui";

// The quality path, made visible: six steps with LIVE status computed from the
// tenant's real data, each with a one-line plain-Italian explanation and a CTA.
// Designed for the operator who has never used the platform.

type StepStatus = "done" | "todo" | "optional";

interface Step {
  title: string;
  what: string; // plain language, no jargon
  to: string;
  cta: string;
  status: StepStatus;
}

const STATUS_UI: Record<StepStatus, { label: string; cls: string }> = {
  done: { label: "Fatto", cls: "bg-emerald-100 text-emerald-700" },
  todo: { label: "Da fare", cls: "bg-amber-100 text-amber-700" },
  optional: { label: "Consigliato", cls: "bg-slate-100 text-slate-500" },
};

export function GuidedPath() {
  const specs = useQuery({ queryKey: ["brand-specs"], queryFn: listBrandSpecs });
  const docs = useQuery({ queryKey: ["method-documents"], queryFn: listMethodDocuments });
  const batches = useQuery({ queryKey: ["batches"], queryFn: listBatches });
  const calrefs = useQuery({ queryKey: ["calref"], queryFn: listCalibrationReferences });
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: () => listTestJobs() });
  const reports = useQuery({ queryKey: ["reports"], queryFn: listReports });

  const ready =
    specs.isSuccess && batches.isSuccess && calrefs.isSuccess && jobs.isSuccess && reports.isSuccess;
  if (!ready) return null;

  const hasSpec = (specs.data?.length ?? 0) > 0;
  const hasDoc = (docs.data?.length ?? 0) > 0;
  const hasBatch = (batches.data ?? []).some((b) => b.status === "active");
  const usableRefs = (calrefs.data ?? []).filter(
    (r) => r.validity === "valid" || r.validity === "expiring"
  );
  const hasRefs = usableRefs.length > 0;
  const allJobs = jobs.data ?? [];
  const hasJob = allJobs.length > 0;
  const hasResult = allJobs.some((j) => j.status !== "created");
  const hasReport = (reports.data?.length ?? 0) > 0;
  const hasLocked = (reports.data ?? []).some((r) => r.locked_at);

  const steps: Step[] = [
    {
      title: "Capitolato del cliente",
      what: "Le tolleranze del brand (grado minimo, ΔE massimo): decidono se una prova è conforme.",
      to: "/brand-specs",
      cta: "Crea capitolato",
      status: hasSpec ? "done" : "todo",
    },
    {
      title: "Norme di prova",
      what: "Il catalogo metodi è già pronto. Se hai la copia licenziata della norma, allegala (PDF).",
      to: "/methods",
      cta: "Vedi norme",
      status: hasDoc ? "done" : "optional",
    },
    {
      title: "Striscia di riferimento (batch zero)",
      what: "La striscia multifibra NON trattata: è il bianco di confronto per la prova di macchia.",
      to: "/batch-zero",
      cta: "Crea batch zero",
      status: hasBatch ? "done" : "todo",
    },
    {
      title: "Kit e tarature",
      what: "Registra lightbox, scala grigi e piastrina con certificato e scadenza. Scaduto = analisi bloccata.",
      to: "/devices",
      cta: "Registra riferimenti",
      status: hasRefs ? "done" : "todo",
    },
    {
      title: "Prova, foto e risultato",
      what: "Crea la prova, fotografa la striscia dopo il test, l'analisi precompila i valori: verifica e salva.",
      to: "/test-jobs",
      cta: hasJob ? "Continua le prove" : "Avvia la prima prova",
      status: hasResult ? "done" : "todo",
    },
    {
      title: "Report sigillato",
      what: "Genera il PDF con sigillo d'integrità, poi finalizzalo: diventa la versione ufficiale verificabile dal cliente.",
      to: hasReport ? "/ledger" : "/test-jobs",
      cta: hasReport ? "Vai al registro" : "Genera dal dettaglio prova",
      status: hasLocked ? "done" : hasReport ? "optional" : "todo",
    },
  ];

  const firstTodo = steps.find((s) => s.status === "todo");
  const doneCount = steps.filter((s) => s.status === "done").length;

  return (
    <Card className="mb-4">
      <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
        <span className="font-medium">Percorso guidato</span>
        <span className="text-xs text-steel">
          {doneCount}/{steps.length} completati
        </span>
      </div>
      <p className="mb-3 text-xs text-steel">
        I passi del controllo qualità, nell'ordine giusto. Verde = fatto. Parti dal primo ambra.
      </p>

      {firstTodo && (
        <div className="mb-3 rounded-lg border border-brand-200 bg-brand-50 p-3">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-brand-600">
            Prossimo passo
          </div>
          <div className="mt-0.5 text-sm font-medium text-ink">{firstTodo.title}</div>
          <p className="mt-0.5 text-xs text-steel">{firstTodo.what}</p>
          <Link to={firstTodo.to} className="mt-2 inline-block">
            <Button>{firstTodo.cta} ›</Button>
          </Link>
        </div>
      )}

      <ol className="space-y-1.5">
        {steps.map((s, i) => {
          const ui = STATUS_UI[s.status];
          return (
            <li key={s.title}>
              <Link
                to={s.to}
                className="flex items-center gap-3 rounded-lg px-2 py-2 transition hover:bg-slate-50"
              >
                <span
                  className={`inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                    s.status === "done" ? "bg-emerald-600 text-white" : "bg-slate-200 text-steel"
                  }`}
                >
                  {s.status === "done" ? "✓" : i + 1}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-medium text-ink">{s.title}</span>
                  <span className="block truncate text-xs text-steel">{s.what}</span>
                </span>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold ${ui.cls}`}
                >
                  {ui.label}
                </span>
              </Link>
            </li>
          );
        })}
      </ol>
    </Card>
  );
}
