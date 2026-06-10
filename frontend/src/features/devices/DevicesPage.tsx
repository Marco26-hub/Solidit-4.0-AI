import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { listDevices, registerDevice } from "@/api/companies";
import {
  createCalibrationReference,
  listCalibrationReferences,
  retireCalibrationReference,
} from "@/api/quality";
import { Badge, Button, Card, ErrorText, Field, PageHeader, TextInput } from "@/components/ui";

const REF_KINDS: { value: string; label: string }[] = [
  { value: "grey_scale", label: "Scala grigia ISO" },
  { value: "white_tile", label: "Piastrina bianca" },
  { value: "colour_target", label: "Target colore" },
  { value: "lightbox", label: "Light box" },
  { value: "other", label: "Altro" },
];

function validityBadge(v: string): { kind: "pass" | "warn" | "fail" | "muted"; label: string } {
  if (v === "valid") return { kind: "pass", label: "valido" };
  if (v === "expiring") return { kind: "warn", label: "in scadenza" };
  if (v === "expired") return { kind: "fail", label: "scaduto" };
  return { kind: "muted", label: "dismesso" };
}

export function DevicesPage() {
  const qc = useQueryClient();
  const devices = useQuery({ queryKey: ["devices"], queryFn: listDevices });
  const [hwid, setHwid] = useState("");
  const [model, setModel] = useState("");
  const [name, setName] = useState("");
  const [mdm, setMdm] = useState(false);

  const create = useMutation({
    mutationFn: () =>
      registerDevice({ hardware_uuid: hwid, model: model || null, name: name || null, mdm_managed: mdm }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["devices"] });
      setHwid("");
      setModel("");
      setName("");
      setMdm(false);
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Devices" subtitle="iPhone autorizzati e calibrazione" />

      <Card>
        <div className="mb-2 font-medium">Dispositivi</div>
        <ErrorText error={devices.error} />
        <div className="divide-y">
          {(devices.data ?? []).map((d) => (
            <div key={d.id} className="flex items-center justify-between py-2 text-sm">
              <div>
                <div className="font-medium">{d.name}</div>
                <div className="text-steel">
                  {d.model ?? "—"} · {d.hardware_uuid}
                </div>
              </div>
              <div className="flex gap-2">
                {d.mdm_managed && <Badge kind="muted">MDM</Badge>}
                <Badge kind={d.active_d65_matrix ? "pass" : "warn"}>
                  {d.active_d65_matrix ? "calibrato D65" : "no calibrazione"}
                </Badge>
              </div>
            </div>
          ))}
          {devices.data?.length === 0 && <p className="py-2 text-steel">Nessun dispositivo.</p>}
        </div>
      </Card>

      <Card>
        <div className="mb-3 font-medium">Registra dispositivo</div>
        <div className="grid gap-3 md:grid-cols-2">
          <Field label="Hardware UUID">
            <TextInput value={hwid} onChange={(e) => setHwid(e.target.value)} />
          </Field>
          <Field label="Modello">
            <TextInput value={model} onChange={(e) => setModel(e.target.value)} placeholder="iPhone 16 Pro" />
          </Field>
          <Field label="Nome">
            <TextInput value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
          <label className="flex items-center gap-2 self-end text-sm text-steel">
            <input type="checkbox" checked={mdm} onChange={(e) => setMdm(e.target.checked)} />
            MDM managed
          </label>
        </div>
        <div className="mt-3">
          <Button type="button" disabled={!hwid || create.isPending} onClick={() => create.mutate()}>
            {create.isPending ? "…" : "Registra"}
          </Button>
        </div>
        <ErrorText error={create.error} />
      </Card>

      <CalibrationReferences />
    </div>
  );
}

function CalibrationReferences() {
  const qc = useQueryClient();
  const refs = useQuery({ queryKey: ["calref"], queryFn: listCalibrationReferences });

  const [kind, setKind] = useState("grey_scale");
  const [code, setCode] = useState("");
  const [cert, setCert] = useState("");
  const [validUntil, setValidUntil] = useState("");

  const create = useMutation({
    mutationFn: () =>
      createCalibrationReference({
        kind,
        code,
        certificate_number: cert || null,
        valid_until: validUntil || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["calref"] });
      setCode("");
      setCert("");
      setValidUntil("");
    },
  });

  const retire = useMutation({
    mutationFn: (id: string) => retireCalibrationReference(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["calref"] }),
  });

  return (
    <Card>
      <div className="mb-1 font-medium">Riferimenti & tarature</div>
      <p className="mb-3 text-xs text-steel">
        Scala grigia, piastrine, target, light box — con certificato e scadenza. L'analisi viene
        BLOCCATA se un riferimento collegato alla cattura è scaduto o dismesso (logica ISO/IEC
        17025).
      </p>
      <ErrorText error={refs.error} />
      <div className="divide-y">
        {(refs.data ?? []).map((r) => {
          const b = validityBadge(r.validity);
          const kindLabel = REF_KINDS.find((k) => k.value === r.kind)?.label ?? r.kind;
          return (
            <div key={r.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
              <div>
                <div className="font-medium">
                  {r.code} <span className="text-steel">· {kindLabel}</span>
                </div>
                <div className="text-xs text-steel">
                  {r.certificate_number ? `cert. ${r.certificate_number} · ` : ""}
                  {r.valid_until ? `scad. ${r.valid_until}` : "senza scadenza"}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge kind={b.kind}>{b.label}</Badge>
                {r.status !== "retired" && (
                  <Button variant="ghost" onClick={() => retire.mutate(r.id)}>
                    Dismetti
                  </Button>
                )}
              </div>
            </div>
          );
        })}
        {refs.data?.length === 0 && <p className="py-2 text-steel">Nessun riferimento.</p>}
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <Field label="Tipo">
          <select
            className="w-full rounded-lg border border-slate-300 px-2 py-1.5 text-sm min-h-[40px]"
            value={kind}
            onChange={(e) => setKind(e.target.value)}
          >
            {REF_KINDS.map((k) => (
              <option key={k.value} value={k.value}>
                {k.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Codice">
          <TextInput value={code} onChange={(e) => setCode(e.target.value)} placeholder="GS-001" />
        </Field>
        <Field label="N° certificato">
          <TextInput value={cert} onChange={(e) => setCert(e.target.value)} />
        </Field>
        <Field label="Valido fino al">
          <TextInput type="date" value={validUntil} onChange={(e) => setValidUntil(e.target.value)} />
        </Field>
      </div>
      <div className="mt-3">
        <Button type="button" disabled={!code || create.isPending} onClick={() => create.mutate()}>
          {create.isPending ? "…" : "Aggiungi riferimento"}
        </Button>
      </div>
      <ErrorText error={create.error} />
    </Card>
  );
}
