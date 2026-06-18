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
    } catch (e) {
      console.error("verifyReport failed", e);
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

  function onFinalize(id: string, number: string) {
    if (
      window.confirm(
        `Finalizzare il report ${number}?\n\nUna volta finalizzato diventa la versione ufficiale e non potrà più essere modificato né rigenerato.`
      )
    )
      finalize.mutate(id);
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Registro report" subtitle="Report digitali con sigillo di integrità SHA-256" />
      <Card>
        <p className="mb-3 text-xs text-steel">
          <b>Verifica integrità</b> = ricontrolla che il PDF non sia stato alterato.{" "}
          <b>Finalizza</b> = blocca il report in versione ufficiale (non più modificabile).{" "}
          <b>Scarica PDF</b> = il documento da inviare.
        </p>
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
                      {r.status === "locked" ? "Bloccato (ufficiale)" : "Bozza"}
                    </Badge>
                  </td>
                  <td>
                    {v ? (
                      <Badge kind={v.valid ? "pass" : "fail"}>{v.valid ? "valido" : "ALTERATO"}</Badge>
                    ) : (
                      <Button variant="ghost" loading={busy === r.id} onClick={() => verify(r.id)}>
                        Verifica integrità
                      </Button>
                    )}
                  </td>
                  <td className="text-right">
                    <div className="flex flex-wrap justify-end gap-2">
                      {r.status !== "locked" && (
                        <Button
                          variant="ghost"
                          loading={finalize.isPending}
                          onClick={() => onFinalize(r.id, r.report_number)}
                        >
                          Finalizza
                        </Button>
                      )}
                      <Button variant="ghost" onClick={() => download(r.id, r.report_number)}>
                        Scarica PDF
                      </Button>
                    </div>
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
