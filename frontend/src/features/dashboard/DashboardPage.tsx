import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listDevices } from "@/api/companies";
import { listBatches, listBrandSpecs, listReports, listTestJobs } from "@/api/quality";
import { Icon } from "@/components/icons";
import { Card, EmptyState, PageHeader, Stat } from "@/components/ui";

export function DashboardPage() {
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
  const isEmpty =
    !jobs.isLoading && all.length === 0 && (specs.data?.length ?? 0) === 0;

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Indicatori del controllo qualità" />

      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <Stat label="Prove totali" value={all.length} icon={<Icon name="clipboard" />} />
        <Stat
          label="Pass rate"
          value={`${passRate}%`}
          hint={`${passed} pass · ${failed} fail`}
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
          label="Dispositivi"
          value={devices.data?.length ?? 0}
          tone="slate"
          icon={<Icon name="device" />}
        />
        <Stat label="Brand specs" value={specs.data?.length ?? 0} icon={<Icon name="tag" />} />
        <Stat
          label="Batch attivi"
          value={(batches.data ?? []).filter((b) => b.status === "active").length}
          tone="amber"
          icon={<Icon name="beaker" />}
        />
      </div>

      {isEmpty && (
        <Card className="mt-4">
          <EmptyState
            title="Inizia da qui"
            hint="Crea una Brand Spec e un Batch Zero, poi registra una prova e genera il report."
          />
          <div className="mt-3 flex flex-wrap gap-2 text-sm">
            <Link to="/brand-specs" className="text-brand-600 underline">
              + Brand spec
            </Link>
            <Link to="/batch-zero" className="text-brand-600 underline">
              + Batch zero
            </Link>
            <Link to="/test-jobs" className="text-brand-600 underline">
              + Prova
            </Link>
          </div>
        </Card>
      )}
    </div>
  );
}
