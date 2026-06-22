import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import {
  estimateFromRgb,
  estimateReflectance,
  ILLUMINANTS,
  type Illuminant,
} from "@/api/spectral";
import { MetamerismPanel } from "./MetamerismPanel";
import { SpectralCurveViewer } from "./SpectralCurveViewer";
import { Button, Card, ErrorText, Field, PageHeader, Select, TextInput } from "@/components/ui";

const clamp = (v: number, lo: number, hi: number) => Math.min(Math.max(v, lo), hi);

type Mode = "lab" | "rgb";

export function SpectralLabPage() {
  const [mode, setMode] = useState<Mode>("rgb");

  // CIELAB inputs
  const [L, setL] = useState("55");
  const [a, setA] = useState("12");
  const [b, setB] = useState("-8");
  const [illuminant, setIlluminant] = useState<Illuminant>("D65");

  // RGB inputs (as from an iPhone pixel)
  const [r, setR] = useState("200");
  const [g, setG] = useState("30");
  const [bl, setBl] = useState("40");

  const estimate = useMutation({
    mutationFn: () =>
      estimateReflectance({
        lab: {
          L: clamp(Number(L) || 0, 0, 100),
          a: clamp(Number(a) || 0, -128, 128),
          b: clamp(Number(b) || 0, -128, 128),
        },
        illuminant,
      }),
  });

  const rgbEstimate = useMutation({
    mutationFn: () =>
      estimateFromRgb({
        rgb: {
          r: clamp(Math.round(Number(r) || 0), 0, 255),
          g: clamp(Math.round(Number(g) || 0), 0, 255),
          b: clamp(Math.round(Number(bl) || 0), 0, 255),
        },
      }),
  });

  const active = mode === "rgb" ? rgbEstimate : estimate;
  const swatch = `rgb(${clamp(Math.round(Number(r) || 0), 0, 255)}, ${clamp(
    Math.round(Number(g) || 0),
    0,
    255
  )}, ${clamp(Math.round(Number(bl) || 0), 0, 255)})`;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Spettro (R&D)"
        subtitle="Stima della curva di riflettanza da colore RGB/CIELAB — strumento sperimentale"
      />

      <Card>
        <p className="text-sm leading-relaxed text-steel">
          Questo strumento <b>stima</b> una curva di riflettanza spettrale a partire da un colore
          (RGB di un pixel iPhone o CIELAB). Non è una misura di spettrofotometro: la ricostruzione
          colore→spettro è <b>sotto-determinata</b> (metamerismo), quindi più spettri diversi possono
          dare lo stesso colore. Il motore (LHTSS) riproduce il colore in modo esatto quando è dentro
          il gamut riflettanza; sui colori molto saturi fuori gamut lo segnala. Il risultato è{" "}
          <b>indicativo, a fini R&D</b>, e <b>non entra nel report sigillato</b>.
        </p>
      </Card>

      <Card>
        <div className="mb-3 inline-flex overflow-hidden rounded-lg border border-slate-300">
          <button
            type="button"
            onClick={() => setMode("rgb")}
            className={`min-h-[40px] px-4 text-sm font-medium ${
              mode === "rgb" ? "bg-brand-600 text-white" : "bg-white text-steel hover:bg-slate-50"
            }`}
          >
            Da RGB (iPhone)
          </button>
          <button
            type="button"
            onClick={() => setMode("lab")}
            className={`min-h-[40px] px-4 text-sm font-medium ${
              mode === "lab" ? "bg-brand-600 text-white" : "bg-white text-steel hover:bg-slate-50"
            }`}
          >
            Da CIELAB
          </button>
        </div>

        {mode === "rgb" ? (
          <>
            <div className="flex flex-wrap items-end gap-3">
              <Field label="R (0–255)">
                <TextInput type="number" min={0} max={255} value={r} onChange={(e) => setR(e.target.value)} />
              </Field>
              <Field label="G (0–255)">
                <TextInput type="number" min={0} max={255} value={g} onChange={(e) => setG(e.target.value)} />
              </Field>
              <Field label="B (0–255)">
                <TextInput type="number" min={0} max={255} value={bl} onChange={(e) => setBl(e.target.value)} />
              </Field>
              <span
                className="h-11 w-11 shrink-0 rounded-lg border border-slate-300"
                style={{ backgroundColor: swatch }}
                aria-label="colore in ingresso"
              />
            </div>
            <div className="mt-3">
              <Button type="button" loading={rgbEstimate.isPending} onClick={() => rgbEstimate.mutate()}>
                Genera curva riflettanza STIMATA (R&D)
              </Button>
            </div>
            <ErrorText error={rgbEstimate.error} />
          </>
        ) : (
          <>
            <div className="grid gap-3 md:grid-cols-4">
              <Field label="L (0–100)">
                <TextInput type="number" step="0.1" min={0} max={100} value={L} onChange={(e) => setL(e.target.value)} />
              </Field>
              <Field label="a (−128…128)">
                <TextInput type="number" step="0.1" min={-128} max={128} value={a} onChange={(e) => setA(e.target.value)} />
              </Field>
              <Field label="b (−128…128)">
                <TextInput type="number" step="0.1" min={-128} max={128} value={b} onChange={(e) => setB(e.target.value)} />
              </Field>
              <Field label="Illuminante">
                <Select value={illuminant} onChange={(e) => setIlluminant(e.target.value as Illuminant)}>
                  {ILLUMINANTS.map((ill) => (
                    <option key={ill} value={ill}>
                      {ill}
                    </option>
                  ))}
                </Select>
              </Field>
            </div>
            <div className="mt-3">
              <Button type="button" loading={estimate.isPending} onClick={() => estimate.mutate()}>
                Genera curva riflettanza STIMATA (R&D)
              </Button>
            </div>
            <ErrorText error={estimate.error} />
          </>
        )}
      </Card>

      {active.data && <SpectralCurveViewer estimate={active.data} />}

      <MetamerismPanel />
    </div>
  );
}
