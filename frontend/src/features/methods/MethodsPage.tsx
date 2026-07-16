import { useMemo, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  downloadMethodDocument,
  listMethodDocuments,
  listTestMethods,
  uploadMethodDocument,
} from "@/api/quality";
import type { TestMethod } from "@/api/types";
import { groupRank, normGroup } from "@/components/MethodSelect";
import { Badge, Button, Card, EmptyState, ErrorText, PageHeader } from "@/components/ui";

export function MethodsPage() {
  const methods = useQuery({ queryKey: ["test-methods"], queryFn: listTestMethods });
  const docs = useQuery({ queryKey: ["method-documents"], queryFn: listMethodDocuments });

  const docByCode = useMemo(() => {
    const m = new Map<string, string>();
    for (const d of docs.data ?? []) m.set(d.test_method_code, d.filename);
    return m;
  }, [docs.data]);

  // group methods by top-level norm body (ISO 105 / AATCC / ASTM / Cuoio / Interni)
  const groups = useMemo(() => {
    const g = new Map<string, TestMethod[]>();
    for (const m of methods.data ?? []) {
      const k = normGroup(m.standard_family);
      (g.get(k) ?? g.set(k, []).get(k)!).push(m);
    }
    for (const list of g.values()) list.sort((a, b) => a.code.localeCompare(b.code));
    return [...g.entries()].sort(
      (a, b) => groupRank(a[0]) - groupRank(b[0]) || a[0].localeCompare(b[0])
    );
  }, [methods.data]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Norme & Metodi"
        subtitle="Catalogo dei metodi di prova (UNI EN ISO 105, AATCC, ASTM, cuoio ISO/IULTCS). Allega la TUA copia licenziata della norma di riferimento per ogni metodo — il documento non viene distribuito da noi."
      />

      <ErrorText error={methods.error || docs.error} />

      {groups.map(([family, list]) => (
        <Card key={family}>
          <div className="mb-2 font-medium">{family}</div>
          <div className="divide-y">
            {list.map((m) => (
              <MethodRow key={m.code} method={m} hasDoc={docByCode.has(m.code)} />
            ))}
          </div>
        </Card>
      ))}

      {methods.data?.length === 0 && <EmptyState title="Nessun metodo" />}
    </div>
  );
}

function MethodRow({ method, hasDoc }: { method: TestMethod; hasDoc: boolean }) {
  const qc = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);

  const upload = useMutation({
    mutationFn: (file: File) => uploadMethodDocument(method.code, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["method-documents"] }),
  });

  const download = useMutation({
    mutationFn: async () => {
      const blob = await downloadMethodDocument(method.code);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${method.code}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    },
  });

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 py-2">
      <div className="min-w-0">
        <div className="text-sm font-medium">{method.name}</div>
        <div className="text-xs text-steel">
          {method.code} · {method.category}
        </div>
        {/* no silent failure: surface upload/download errors on the row */}
        <ErrorText error={upload.error || download.error} />
      </div>
      <div className="flex items-center gap-2">
        {hasDoc ? <Badge kind="pass">copia allegata</Badge> : <Badge kind="muted">da allegare</Badge>}
        {hasDoc && (
          <Button variant="ghost" disabled={download.isPending} onClick={() => download.mutate()}>
            {download.isPending ? "…" : "Scarica"}
          </Button>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) upload.mutate(f);
            e.target.value = "";
          }}
        />
        <Button
          variant="ghost"
          disabled={upload.isPending}
          onClick={() => inputRef.current?.click()}
        >
          {upload.isPending ? "…" : hasDoc ? "Sostituisci" : "Carica norma"}
        </Button>
      </div>
    </div>
  );
}
