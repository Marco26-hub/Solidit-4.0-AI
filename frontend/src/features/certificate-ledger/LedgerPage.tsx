import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { downloadReport, finalizeReport, listReports, verifyReport } from "@/api/quality";
import type { ReportVerify } from "@/api/types";
import { Badge, Button, Card, ErrorText, PageHeader } from "@/components/ui";

export function LedgerPage() {
  const qc = useQueryClient();
  const reports = useQuery({ queryKey: ["reports"], queryFn: listReports });
  const [verified, setVerified] = useState<Record<string, ReportVerify>>({});
  const [busy, setBusy] = useState<string | null>(null);

  const finalize = useMutation({
    mutationFn: (id: string) => finalizeReport(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reports"] }),
  });

  async function verify(id: string) {
    setBusy(id);
    try {
      const v = await verifyReport(id);
      setVerified((m) => ({ ...m, [id]: v }));
    } finally {
      setBusy(null);
    }
  }

  async function download(id: string, name: string) {
    const blob = await downloadReport(id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${name}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Certificate Ledger" subtitle="Report digitali con sigillo di integrità SHA-256" />
      <Card>
        <ErrorText error={reports.error} />
        <div className="overflow-x-auto">
        <table className="w-full min-w-[480px] text-sm">
          <thead className="text-left text-steel">
            <tr>
              <th className="py-1">Report N.</th>
              <th>SHA-256</th>
              <th>Stato</th>
              <th>Verifica</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {(reports.data ?? []).map((r) => {
              const v = verified[r.id];
              return (
                <tr key={r.id} className="border-t align-middle">
                  <td className="py-1.5 font-medium">{r.report_number}</td>
                  <td className="font-mono text-xs text-steel">{r.sha256_hash.slice(0, 16)}…</td>
                  <td>
                    <Badge kind={r.status === "locked" ? "pass" : "muted"}>
                      {r.status === "locked" ? "bloccato (ufficiale)" : r.status}
                    </Badge>
                  </td>
                  <td>
                    {v ? (
                      <Badge kind={v.valid ? "pass" : "fail"}>{v.valid ? "valido" : "ALTERATO"}</Badge>
                    ) : (
                      <Button variant="ghost" disabled={busy === r.id} onClick={() => verify(r.id)}>
                        {busy === r.id ? "…" : "verifica"}
                      </Button>
                    )}
                  </td>
                  <td className="text-right">
                    {r.status !== "locked" && (
                      <Button
                        variant="ghost"
                        disabled={finalize.isPending}
                        onClick={() => finalize.mutate(r.id)}
                      >
                        finalizza
                      </Button>
                    )}
                    <Button variant="ghost" onClick={() => download(r.id, r.report_number)}>
                      PDF
                    </Button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        </div>
        {reports.data?.length === 0 && <p className="py-2 text-steel">Nessun report.</p>}
      </Card>
    </div>
  );
}
