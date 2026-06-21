import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { estimateReflectance, ILLUMINANTS, type Illuminant } from "@/api/spectral";
import { SpectralCurveViewer } from "./SpectralCurveViewer";
import { Button, Card, ErrorText, Field, PageHeader, Select, TextInput } from "@/components/ui";

const clamp = (v: number, lo: number, hi: number) => Math.min(Math.max(v, lo), hi);

export function SpectralLabPage() {
  const [L, setL] = useState("55");
  const [a, setA] = useState("12");
  const [b, setB] = useState("-8");
  const [illuminant, setIlluminant] = useState<Illuminant>("D65");

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

  const valid = L !== "" && a !== "" && b !== "";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Spettro (R&D)"
        subtitle="Stima della curva di riflettanza da valori CIELAB — strumento sperimentale"
      />

      <Card>
        <p className="text-sm leading-relaxed text-steel">
          Questo strumento <b>stima</b> una curva di riflettanza spettrale a partire da un colore
          CIELAB. Non è una misura di spettrofotometro: la ricostruzione RGB/Lab→spettro è{" "}
          <b>sotto-determinata</b> (metamerismo), quindi più spettri diversi possono dare lo stesso
          colore. Il risultato è <b>indicativo, a fini R&D</b>, e <b>non entra nel report sigillato</b>.
          Non chiamarlo "misura" o "spettrofotometro".
        </p>
      </Card>

      <Card>
        <div className="mb-3 font-medium">Colore CIELAB in ingresso</div>
        <div className="grid gap-3 md:grid-cols-4">
          <Field label="L (0–100)">
            <TextInput
              type="number"
              inputMode="decimal"
              step="0.1"
              min={0}
              max={100}
              value={L}
              onChange={(e) => setL(e.target.value)}
            />
          </Field>
          <Field label="a (−128…128)">
            <TextInput
              type="number"
              inputMode="decimal"
              step="0.1"
              min={-128}
              max={128}
              value={a}
              onChange={(e) => setA(e.target.value)}
            />
          </Field>
          <Field label="b (−128…128)">
            <TextInput
              type="number"
              inputMode="decimal"
              step="0.1"
              min={-128}
              max={128}
              value={b}
              onChange={(e) => setB(e.target.value)}
            />
          </Field>
          <Field label="Illuminante">
            <Select
              value={illuminant}
              onChange={(e) => setIlluminant(e.target.value as Illuminant)}
            >
              {ILLUMINANTS.map((ill) => (
                <option key={ill} value={ill}>
                  {ill}
                </option>
              ))}
            </Select>
          </Field>
        </div>

        <div className="mt-3">
          <Button
            type="button"
            loading={estimate.isPending}
            disabled={!valid}
            onClick={() => estimate.mutate()}
          >
            Genera curva riflettanza STIMATA (R&D)
          </Button>
        </div>
        <ErrorText error={estimate.error} />
      </Card>

      {estimate.data && <SpectralCurveViewer estimate={estimate.data} />}
    </div>
  );
}
