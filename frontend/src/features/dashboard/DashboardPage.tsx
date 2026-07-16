import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { listDevices } from "@/api/companies";
import { listBatches, listBrandSpecs, listReports, listTestJobs } from "@/api/quality";
import { Icon } from "@/components/icons";
import { Button, PageHeader, Stat } from "@/components/ui";
import { GuidedPath } from "./GuidedPath";

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

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Indicatori del controllo qualità" />

      <Button className="mb-4 w-full sm:w-auto" onClick={() => navigate("/test-jobs")}>
        <Icon name="clipboard" /> Avvia una nuova prova
      </Button>

      {/* the full quality path with live status — the novice operator's map */}
      <GuidedPath />

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
