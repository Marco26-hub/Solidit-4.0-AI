import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";

import { listDevices } from "@/api/companies";
import { listBatches, listBrandSpecs, listReports, listTestJobs } from "@/api/quality";
import { Icon } from "@/components/icons";
import { Button, Card, PageHeader, Stat } from "@/components/ui";

export function DashboardPage() {
  const navigate = useNavigate();
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: () => listTestJobs() });
  const reports = useQuery({ queryKey: ["reports"], queryFn: listReports });
  const devices = useQuery({ queryKey: ["devices"], queryFn: listDevices });
  const specs = useQuery({ queryKey: ["brand-specs"], queryFn: listBrandSpecs });
  const batches = useQuery({ queryKey: ["batches"], queryFn: listBatches });

  const all = jobs.data ?? [];
  const passed = all.filter((j) => j.status === "passed").length;
  const failed = all.filter((j) => j.status === "failed").length;
  const decided = passed + failed;
  const passRate = decided ? Math.round((passed / decided) * 100) : 0;

  // "Prossimo passo": one prominent action based on what's still missing,
  // visible until the first report exists.
  const hasSpec = (specs.data?.length ?? 0) > 0;
  const hasBatch = (batches.data ?? []).some((b) => b.status === "active");
  const hasJob = all.length > 0;
  const hasReport = (reports.data?.length ?? 0) > 0;
  const ready = jobs.isSuccess && specs.isSuccess && batches.isSuccess && reports.isSuccess;
  let next: { label: string; to: string; why: string } | null = null;
  if (ready && !hasReport) {
    if (!hasSpec)
      next = {
        label: "Crea il primo capitolato brand",
        to: "/brand-specs",
        why: "Le regole del capitolato decidono se una prova è conforme. Senza, la prova mostra i valori senza verdetto.",
      };
    else if (!hasBatch)
      next = {
        label: "Crea un Batch Zero",
        to: "/batch-zero",
        why: "La striscia multifibra di riferimento serve prima di una prova di macchia.",
      };
    else if (!hasJob)
      next = { label: "Avvia la prima prova", to: "/test-jobs", why: "Tutto pronto: registra la prima prova." };
    else
      next = {
        label: "Genera il primo report",
        to: "/test-jobs",
        why: "Hai una prova: apri la prova, salva il risultato e genera il report.",
      };
  }

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Indicatori del controllo qualità" />

      <Button className="mb-4 w-full sm:w-auto" onClick={() => navigate("/test-jobs")}>
        <Icon name="clipboard" /> Avvia una nuova prova
      </Button>

      {next && (
        <Card className="mb-4 border-brand-200 bg-brand-50">
          <div className="text-xs font-medium uppercase tracking-wide text-brand-600">
            Prossimo passo
          </div>
          <p className="mt-1 text-sm text-steel">{next.why}</p>
          <Link to={next.to} className="mt-3 inline-block">
            <Button>{next.label} ›</Button>
          </Link>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <Stat label="Prove totali" value={all.length} icon={<Icon name="clipboard" />} />
        <Stat
          label="Esiti positivi"
          value={`${passRate}%`}
          hint={`${passed} conformi · ${failed} non conformi`}
          tone="emerald"
          icon={<Icon name="check" />}
        />
        <Stat
          label="Report emessi"
          value={reports.data?.length ?? 0}
          tone="slate"
          icon={<Icon name="doc" />}
        />
        <Stat
          label="Dispositivi e kit"
          value={devices.data?.length ?? 0}
          tone="slate"
          icon={<Icon name="device" />}
        />
        <Stat label="Brand spec" value={specs.data?.length ?? 0} icon={<Icon name="tag" />} />
        <Stat
          label="Batch attivi"
          value={(batches.data ?? []).filter((b) => b.status === "active").length}
          tone="amber"
          icon={<Icon name="beaker" />}
        />
      </div>
    </div>
  );
}
