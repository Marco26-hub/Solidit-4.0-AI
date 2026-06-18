import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { CalibrationReference } from "@/api/types";
import { listDevices, registerDevice } from "@/api/companies";
import {
  createCalibrationReference,
  listCalibrationReferences,
  retireCalibrationReference,
} from "@/api/quality";
import { Icon, type IconName } from "@/components/icons";
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
} from "@/components/ui";

// ── Guided catalog of physical reference standards ──────────────────────────
// Operators pick by PURPOSE then by INSTRUMENT (real names + standard badges),
// never by an abstract class. Public identifiers only (no copyrighted text).
type RefGroup = { key: string; title: string; subtitle: string; icon: IconName };
const REF_GROUPS: RefGroup[] = [
  {
    key: "anchor",
    title: "Correzione colore",
    subtitle: "Ancore con valore CIELAB certificato (piastrina bianca, target colore).",
    icon: "drop",
  },
  {
    key: "visual",
    title: "Valutazione visiva",
    subtitle: "Scale di confronto per assegnare un grado (grigi A02/A03, scala dei blu).",
    icon: "eye",
  },
  {
    key: "light",
    title: "Condizioni di luce",
    subtitle: "Cabina di luce e illuminanti.",
    icon: "sun",
  },
  {
    key: "other",
    title: "Materiali di consumo / altro",
    subtitle: "Multifibre, sfregamento, sudore, detersivo (lotto + scadenza).",
    icon: "beaker",
  },
];

type Instrument = {
  id: string;
  group: string;
  kind: string;
  name: string;
  badge?: string;
  oneLiner: string;
  helper: string;
  needsLab?: boolean;
  needsPatches?: boolean;
  needsIlluminants?: boolean;
  needsSeries?: boolean;
  needsConsumable?: boolean;
  showCertObs?: boolean;
  defaults?: {
    subtype?: string;
    series?: string;
    standard?: string;
    illuminants?: string[];
    cert_illuminant?: string;
    cert_observer?: string;
  };
};

const INSTRUMENTS: Instrument[] = [
  {
    id: "white_tile",
    group: "anchor",
    kind: "white_tile",
    name: "Piastrina bianca (mattonella ceramica)",
    badge: "D65/10°",
    oneLiner: "Tara il bianco delle foto col valore certificato.",
    helper:
      "Inserisci L*a*b* esattamente come sul certificato di taratura: àncorano la correzione colore delle foto. Validi solo sotto l'illuminante/osservatore indicati (di norma D65/10°). Una piastrina sporca o graffiata falsa ogni misura — rispetta la scadenza.",
    needsLab: true,
    showCertObs: true,
    defaults: { cert_illuminant: "D65", cert_observer: "10°" },
  },
  {
    id: "colour_target",
    group: "anchor",
    kind: "colour_target",
    name: "Target colore multi-patch (es. ColorChecker)",
    badge: "multi-patch",
    oneLiner: "Profila la fotocamera su tutta la gamma, non solo sul bianco.",
    helper:
      "Inserisci i valori certificati di ciascun tassello. Usa i valori del LOTTO di QUESTO target (non valori generici): i target sbiadiscono. Imposta la scadenza del lotto.",
    needsPatches: true,
    showCertObs: true,
    defaults: { cert_illuminant: "D65", cert_observer: "10°" },
  },
  {
    id: "grey_staining",
    group: "visual",
    kind: "grey_scale",
    name: "Scala dei grigi — macchiatura / scarico",
    badge: "ISO 105-A03",
    oneLiner: "Quanto colore si trasferisce sul bianco adiacente.",
    helper:
      "Scala visiva per lo SCARICO/MACCHIATURA (lavaggio, sudore, sfregamento). Assegna un GRADO (5 = nessuna macchia → 1 = forte), non porta valori L*a*b*. NON è la scala per la degradazione (A02).",
    defaults: { subtype: "A03", standard: "ISO 105-A03" },
  },
  {
    id: "grey_change",
    group: "visual",
    kind: "grey_scale",
    name: "Scala dei grigi — degradazione / variazione",
    badge: "ISO 105-A02",
    oneLiner: "Quanto cambia colore il campione stesso dopo il trattamento.",
    helper:
      "Scala visiva per la DEGRADAZIONE/VARIAZIONE del campione vs originale. Assegna un GRADO (5 = nessuna variazione → 1 = severa), non porta valori L*a*b*. NON è la scala per la macchiatura (A03).",
    defaults: { subtype: "A02", standard: "ISO 105-A02" },
  },
  {
    id: "blue_wool",
    group: "visual",
    kind: "blue_wool",
    name: "Scala dei blu (lana blu) — solidità alla luce",
    badge: "ISO 105-B01/B02",
    oneLiner: "Riferimento esposto INSIEME al campione alla luce.",
    helper:
      "Riferimento per la solidità alla LUCE. Scegli la numerazione stampata sulle tue strisce — Europea ISO 1–8 o Americana AATCC L2–L9 — per non confondere le serie. Non c'entra con le scale dei grigi del risultato.",
    needsSeries: true,
    defaults: { series: "iso_1_8" },
  },
  {
    id: "lightbox",
    group: "light",
    kind: "lightbox",
    name: "Cabina di luce",
    badge: "D65/TL84/UV…",
    oneLiner: "Illuminazione controllata per valutazione e cattura.",
    helper:
      "Seleziona TUTTI gli illuminanti installati: la luce è un insieme, non uno solo. La validità dipende più dalle ORE LAMPADA che dal calendario. Ricorda se l'UV è acceso: cambia il risultato.",
    needsIlluminants: true,
    defaults: { illuminants: ["D65"] },
  },
  {
    id: "other",
    group: "other",
    kind: "other",
    name: "Materiale di consumo / altro",
    oneLiner: "Multifibre, panno sfregamento, sudore, detersivo.",
    helper:
      "Per materiali di consumo o riferimenti non classificati. Registra lotto e scadenza: soluzioni sudore/pH e detersivo ECE scadono e la scadenza blocca l'analisi se collegati a una cattura.",
    needsConsumable: true,
  },
];

const ILLUMINANTS = ["D65", "TL84", "UV", "A", "CWF", "U30", "U35", "Horizon"];
const CONSUMABLES: { value: string; label: string }[] = [
  { value: "multifibre", label: "Tessuto multifibre (ISO 105-F)" },
  { value: "crock_cloth", label: "Panno per sfregamento (ISO 105-X12)" },
  { value: "perspiration", label: "Soluzione sudore/pH (ISO 105-E04)" },
  { value: "detergent", label: "Detersivo ECE (ISO 105-C)" },
  { value: "altro", label: "Altro" },
];

function describeRef(r: CalibrationReference): { name: string; badge?: string } {
  if (r.kind === "grey_scale") {
    return {
      name: r.subtype === "A02" ? "Scala grigi — degradazione" : "Scala grigi — macchiatura",
      badge: r.standard ?? (r.subtype === "A02" ? "ISO 105-A02" : "ISO 105-A03"),
    };
  }
  const names: Record<string, string> = {
    white_tile: "Piastrina bianca",
    colour_target: "Target colore",
    blue_wool: "Scala dei blu",
    lightbox: "Cabina di luce",
    other: "Consumabile / altro",
  };
  let badge = r.standard ?? undefined;
  if (r.kind === "lightbox" && r.illuminants?.length) badge = r.illuminants.join("/");
  if (r.kind === "blue_wool" && r.series)
    badge = r.series === "aatcc_l2_l9" ? "AATCC L2–L9" : "ISO 1–8";
  return { name: names[r.kind] ?? r.kind, badge };
}

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
      <PageHeader title="Dispositivi e standard" subtitle="iPhone autorizzati e riferimenti fisici per il colore" />

      <Card>
        <div className="mb-1 font-medium">iPhone autorizzati</div>
        <p className="mb-2 text-xs text-steel">
          I telefoni autorizzati a scattare le foto delle prove. Registra qui ogni iPhone usato in
          laboratorio.
        </p>
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
                  {d.active_d65_matrix ? "calibrato D65" : "da calibrare"}
                </Badge>
              </div>
            </div>
          ))}
          {devices.data?.length === 0 && (
            <p className="py-2 text-steel">
              Nessun iPhone registrato. Aggiungi qui sotto il telefono che userai per le foto.
            </p>
          )}
        </div>
      </Card>

      <Card>
        <div className="mb-3 font-medium">Registra iPhone</div>
        <div className="grid gap-3 md:grid-cols-2">
          <Field
            label="Identificativo iPhone"
            required
            hint="Codice univoco dell'iPhone — nell'app Solidità: Impostazioni → Info dispositivo."
          >
            <TextInput value={hwid} onChange={(e) => setHwid(e.target.value)} placeholder="es. 00008130-0011…" />
          </Field>
          <Field label="Modello">
            <TextInput value={model} onChange={(e) => setModel(e.target.value)} placeholder="iPhone 16 Pro" />
          </Field>
          <Field label="Nome">
            <TextInput
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="es. iPhone reparto tintoria"
            />
          </Field>
          <label className="flex items-center gap-2 self-end text-sm text-steel">
            <input type="checkbox" checked={mdm} onChange={(e) => setMdm(e.target.checked)} />
            Gestito da MDM aziendale (lascia deselezionato se non sai cosa significa)
          </label>
        </div>
        <div className="mt-3">
          <Button type="button" loading={create.isPending} disabled={!hwid} onClick={() => create.mutate()}>
            Registra
          </Button>
          {!hwid && <Hint>Inserisci l'identificativo dell'iPhone per registrarlo.</Hint>}
        </div>
        <ErrorText error={create.error} />
      </Card>

      <div className="pt-1">
        <h2 className="text-base font-semibold text-ink">Riferimenti fisici per il colore</h2>
        <p className="text-xs text-steel">
          Scale grigi, scala dei blu, piastrina, cabina di luce — con certificato e scadenza.
        </p>
      </div>
      <CalibrationReferences />
    </div>
  );
}

const BLANK_FORM = {
  code: "",
  cert: "",
  validUntil: "",
  desc: "",
  L: "",
  a: "",
  b: "",
  lampHours: "",
  certIll: "",
  certObs: "",
};
type PatchRow = { patch_id: string; L: string; a: string; b: string };

function CalibrationReferences() {
  const qc = useQueryClient();
  const refs = useQuery({ queryKey: ["calref"], queryFn: listCalibrationReferences });

  const [groupKey, setGroupKey] = useState<string | null>(null);
  const [instrId, setInstrId] = useState<string | null>(null);
  const [form, setForm] = useState(BLANK_FORM);
  const [series, setSeries] = useState("iso_1_8");
  const [illum, setIllum] = useState<string[]>([]);
  const [consumable, setConsumable] = useState("multifibre");
  const [patches, setPatches] = useState<PatchRow[]>([{ patch_id: "", L: "", a: "", b: "" }]);

  const instr = INSTRUMENTS.find((i) => i.id === instrId) ?? null;

  const reset = () => {
    setGroupKey(null);
    setInstrId(null);
    setForm(BLANK_FORM);
    setSeries("iso_1_8");
    setIllum([]);
    setConsumable("multifibre");
    setPatches([{ patch_id: "", L: "", a: "", b: "" }]);
  };

  const pick = (i: Instrument) => {
    setInstrId(i.id);
    setForm({
      ...BLANK_FORM,
      certIll: i.defaults?.cert_illuminant ?? "",
      certObs: i.defaults?.cert_observer ?? "",
    });
    setSeries(i.defaults?.series ?? "iso_1_8");
    setIllum(i.defaults?.illuminants ?? []);
    setConsumable("multifibre");
    setPatches([{ patch_id: "", L: "", a: "", b: "" }]);
  };

  const setF = (patch: Partial<typeof BLANK_FORM>) => setForm((f) => ({ ...f, ...patch }));
  const toggleIllum = (x: string) =>
    setIllum((arr) => (arr.includes(x) ? arr.filter((v) => v !== x) : [...arr, x]));

  const create = useMutation({
    mutationFn: () => {
      if (!instr) throw new Error("Nessuno strumento selezionato");
      const labOk = form.L !== "" && form.a !== "" && form.b !== "";
      return createCalibrationReference({
        kind: instr.kind,
        code: form.code,
        description: form.desc || null,
        certificate_number: form.cert || null,
        valid_until: form.validUntil || null,
        reference_values:
          instr.needsLab && labOk
            ? { L: Number(form.L), a: Number(form.a), b: Number(form.b) }
            : null,
        subtype: instr.defaults?.subtype ?? null,
        standard: instr.defaults?.standard ?? null,
        series: instr.needsSeries ? series : null,
        illuminants: instr.needsIlluminants ? illum : null,
        lamp_hours: instr.needsIlluminants && form.lampHours ? Number(form.lampHours) : null,
        cert_illuminant: instr.showCertObs ? form.certIll || null : null,
        cert_observer: instr.showCertObs ? form.certObs || null : null,
        consumable_type: instr.needsConsumable ? consumable : null,
        patch_values: instr.needsPatches
          ? patches
              .filter((p) => p.patch_id && p.L !== "" && p.a !== "" && p.b !== "")
              .map((p) => ({ patch_id: p.patch_id, L: Number(p.L), a: Number(p.a), b: Number(p.b) }))
          : null,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["calref"] });
      reset();
    },
  });

  const retire = useMutation({
    mutationFn: (id: string) => retireCalibrationReference(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["calref"] }),
  });

  const labOk = form.L !== "" && form.a !== "" && form.b !== "";
  const canSave = Boolean(form.code) && (!instr?.needsLab || labOk) && !create.isPending;

  return (
    <Card>
      <div className="mb-1 font-medium">Standard & riferimenti</div>
      <p className="mb-3 text-xs text-steel">
        Carica i tuoi standard fisici (scale grigi, scala dei blu, piastrina, target, cabina di
        luce) con certificato e scadenza. L'analisi viene BLOCCATA se un riferimento collegato a una
        cattura è scaduto o dismesso (logica ISO/IEC 17025).
      </p>

      {/* saved references */}
      <ErrorText error={refs.error} />
      <div className="divide-y">
        {(refs.data ?? []).map((r) => {
          const b = validityBadge(r.validity);
          const d = describeRef(r);
          return (
            <div key={r.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
              <div>
                <div className="font-medium">
                  {r.code} <span className="text-steel">· {d.name}</span>
                  {d.badge && (
                    <span className="ml-1 rounded bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium text-slate-600">
                      {d.badge}
                    </span>
                  )}
                </div>
                <div className="text-xs text-steel">
                  {r.certificate_number ? `cert. ${r.certificate_number} · ` : ""}
                  {r.valid_until ? `scad. ${r.valid_until}` : "senza scadenza"}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge kind={b.kind}>{b.label}</Badge>
                {r.status !== "retired" && (
                  <Button
                    variant="ghost"
                    onClick={() => {
                      if (
                        window.confirm(
                          `Dismettere lo standard «${r.code}»?\n\nNon potrà più essere collegato a nuove catture e le prove che lo usano verranno bloccate.`
                        )
                      )
                        retire.mutate(r.id);
                    }}
                  >
                    Dismetti
                  </Button>
                )}
              </div>
            </div>
          );
        })}
        {refs.data?.length === 0 && (
          <p className="py-2 text-steel">
            Nessuno standard caricato. Carica scale grigi, scala dei blu, piastrina o cabina di luce
            — inizia da «Carica uno standard».
          </p>
        )}
      </div>

      {/* guided add: step 1 purpose → step 2 instrument → form */}
      <div className="mt-4 border-t pt-4">
        {!instr ? (
          <>
            <div className="mb-2 text-sm font-medium">Carica uno standard</div>
            {!groupKey ? (
              <div className="grid gap-2">
                {REF_GROUPS.map((g) => (
                  <button
                    key={g.key}
                    onClick={() => setGroupKey(g.key)}
                    className="flex items-center gap-3 rounded-xl border border-slate-200 p-3 text-left hover:bg-slate-50"
                  >
                    <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-brand-50 text-brand-600">
                      <Icon name={g.icon} />
                    </span>
                    <span>
                      <span className="block text-sm font-medium text-ink">{g.title}</span>
                      <span className="block text-xs text-steel">{g.subtitle}</span>
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <>
                <button
                  onClick={() => setGroupKey(null)}
                  className="mb-2 text-xs font-medium text-brand-600"
                >
                  ← Cambia categoria
                </button>
                <div className="grid gap-2">
                  {INSTRUMENTS.filter((i) => i.group === groupKey).map((i) => (
                    <button
                      key={i.id}
                      onClick={() => pick(i)}
                      className="rounded-xl border border-slate-200 p-3 text-left hover:bg-slate-50"
                    >
                      <span className="flex items-center gap-2">
                        <span className="text-sm font-medium text-ink">{i.name}</span>
                        {i.badge && (
                          <span className="rounded bg-brand-50 px-1.5 py-0.5 text-[11px] font-medium text-brand-600">
                            {i.badge}
                          </span>
                        )}
                      </span>
                      <span className="mt-0.5 block text-xs text-steel">{i.oneLiner}</span>
                    </button>
                  ))}
                </div>
              </>
            )}
          </>
        ) : (
          <>
            <button onClick={reset} className="mb-2 text-xs font-medium text-brand-600">
              ← Cambia strumento
            </button>
            <div className="text-sm font-medium text-ink">
              {instr.name}
              {instr.badge && (
                <span className="ml-1 rounded bg-brand-50 px-1.5 py-0.5 text-[11px] font-medium text-brand-600">
                  {instr.badge}
                </span>
              )}
            </div>
            <p className="mt-1 text-xs text-steel">{instr.helper}</p>

            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <Field label="Codice">
                <TextInput
                  value={form.code}
                  onChange={(e) => setF({ code: e.target.value })}
                  placeholder="es. GS-001"
                />
              </Field>
              <Field label="N° certificato / lotto">
                <TextInput value={form.cert} onChange={(e) => setF({ cert: e.target.value })} />
              </Field>
              <Field label="Valido fino al">
                <TextInput
                  type="date"
                  value={form.validUntil}
                  onChange={(e) => setF({ validUntil: e.target.value })}
                />
              </Field>
              <Field label="Produttore / descrizione">
                <TextInput value={form.desc} onChange={(e) => setF({ desc: e.target.value })} />
              </Field>
            </div>

            {instr.needsSeries && (
              <div className="mt-3">
                <Field label="Numerazione serie">
                  <Select value={series} onChange={(e) => setSeries(e.target.value)}>
                    <option value="iso_1_8">Europea — ISO 1–8</option>
                    <option value="aatcc_l2_l9">Americana — AATCC L2–L9</option>
                  </Select>
                </Field>
              </div>
            )}

            {instr.needsIlluminants && (
              <div className="mt-3">
                <div className="text-sm font-medium text-steel">Illuminanti installati</div>
                <div className="mt-1 flex flex-wrap gap-2">
                  {ILLUMINANTS.map((x) => {
                    const on = illum.includes(x);
                    return (
                      <button
                        key={x}
                        onClick={() => toggleIllum(x)}
                        className={`min-h-[40px] rounded-lg border px-3 text-sm font-medium ${
                          on
                            ? "border-brand-500 bg-brand-50 text-brand-600"
                            : "border-slate-300 text-steel"
                        }`}
                      >
                        {x}
                      </button>
                    );
                  })}
                </div>
                <div className="mt-2 sm:max-w-xs">
                  <Field label="Ore lampada (opz.)">
                    <TextInput
                      type="number"
                      inputMode="decimal"
                      value={form.lampHours}
                      onChange={(e) => setF({ lampHours: e.target.value })}
                    />
                  </Field>
                </div>
              </div>
            )}

            {instr.needsConsumable && (
              <div className="mt-3">
                <Field label="Tipo consumabile">
                  <Select value={consumable} onChange={(e) => setConsumable(e.target.value)}>
                    {CONSUMABLES.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>
            )}

            {instr.needsLab && (
              <div className="mt-3">
                <div className="text-xs text-steel">
                  Lab certificato (dal certificato del riferimento) — àncora la correzione colore
                  in-frame.
                </div>
                <div className="mt-1 grid grid-cols-3 gap-2 sm:max-w-xs">
                  {(["L", "a", "b"] as const).map((k) => (
                    <TextInput
                      key={k}
                      type="number"
                      inputMode="decimal"
                      step="0.01"
                      placeholder={`cert. ${k}`}
                      value={form[k]}
                      onChange={(e) => setF({ [k]: e.target.value })}
                    />
                  ))}
                </div>
              </div>
            )}

            {instr.showCertObs && (
              <div className="mt-3 grid grid-cols-2 gap-2 sm:max-w-xs">
                <Field label="Illuminante cert.">
                  <TextInput value={form.certIll} onChange={(e) => setF({ certIll: e.target.value })} />
                </Field>
                <Field label="Osservatore cert.">
                  <TextInput value={form.certObs} onChange={(e) => setF({ certObs: e.target.value })} />
                </Field>
              </div>
            )}

            {instr.needsPatches && (
              <div className="mt-3">
                <div className="text-xs text-steel">
                  Valori certificati per tassello (almeno uno). Aggiungi una riga per ogni patch.
                </div>
                <div className="mt-1 space-y-2">
                  {patches.map((p, i) => (
                    <div key={i} className="flex flex-wrap items-center gap-2">
                      <TextInput
                        placeholder="patch (es. A1)"
                        className="basis-full sm:flex-1 sm:basis-0"
                        value={p.patch_id}
                        onChange={(e) =>
                          setPatches((rs) =>
                            rs.map((r, idx) => (idx === i ? { ...r, patch_id: e.target.value } : r))
                          )
                        }
                      />
                      {(["L", "a", "b"] as const).map((k) => (
                        <TextInput
                          key={k}
                          type="number"
                          inputMode="decimal"
                          step="0.01"
                          placeholder={k}
                          className="min-w-0 flex-1"
                          value={p[k]}
                          onChange={(e) =>
                            setPatches((rs) =>
                              rs.map((r, idx) => (idx === i ? { ...r, [k]: e.target.value } : r))
                            )
                          }
                        />
                      ))}
                      <Button
                        variant="ghost"
                        className="shrink-0 px-3"
                        aria-label="rimuovi patch"
                        onClick={() => setPatches((rs) => rs.filter((_, idx) => idx !== i))}
                      >
                        ✕
                      </Button>
                    </div>
                  ))}
                </div>
                <Button
                  variant="ghost"
                  className="mt-2"
                  onClick={() =>
                    setPatches((rs) => [...rs, { patch_id: "", L: "", a: "", b: "" }])
                  }
                >
                  + patch
                </Button>
              </div>
            )}

            <div className="mt-4">
              <Button type="button" loading={create.isPending} disabled={!canSave} onClick={() => create.mutate()}>
                Salva standard
              </Button>
              {!form.code ? (
                <Hint>Inserisci almeno il Codice per salvare.</Hint>
              ) : instr?.needsLab && !labOk ? (
                <Hint>Inserisci i valori L*a*b* dal certificato per salvare.</Hint>
              ) : null}
            </div>
            <ErrorText error={create.error} />
          </>
        )}
      </div>
    </Card>
  );
}
