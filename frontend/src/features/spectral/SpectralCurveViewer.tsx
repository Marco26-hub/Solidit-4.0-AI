import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { renderUnder, ILLUMINANTS, type Illuminant, type ReflectanceEstimate } from "@/api/spectral";
import { Badge, Button, ErrorText } from "@/components/ui";

// Inline SVG line chart of the ESTIMATED reflectance curve. No external chart
// lib — the curve is x = wavelength (nm), y = reflectance (0..1). It is an
// estimate, NOT a spectrophotometer measurement (project rule 7).

const VIEW_W = 600;
const VIEW_H = 280;
const PAD = { top: 16, right: 16, bottom: 36, left: 44 };
const PLOT_W = VIEW_W - PAD.left - PAD.right;
const PLOT_H = VIEW_H - PAD.top - PAD.bottom;

function fmtLab(lab: number[]): string {
  if (!lab || lab.length < 3) return "—";
  return `L ${lab[0].toFixed(1)} · a ${lab[1].toFixed(1)} · b ${lab[2].toFixed(1)}`;
}

function ReflectanceChart({ estimate }: { estimate: ReflectanceEstimate }) {
  const { wavelengths_nm: xs, reflectance: ys } = estimate;

  const geom = useMemo(() => {
    const n = Math.min(xs.length, ys.length);
    if (n === 0) return null;
    const xMin = Math.min(...xs);
    const xMax = Math.max(...xs);
    const sx = (x: number) => PAD.left + ((x - xMin) / (xMax - xMin || 1)) * PLOT_W;
    // y axis is fixed 0..1 (reflectance fraction) so curves are comparable
    const sy = (y: number) => PAD.top + (1 - Math.min(Math.max(y, 0), 1)) * PLOT_H;
    // drop any non-finite point so the polyline never gets a NaN coordinate
    const pts = Array.from({ length: n }, (_, i) => [xs[i], ys[i]] as const)
      .filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y))
      .map(([x, y]) => `${sx(x).toFixed(1)},${sy(y).toFixed(1)}`)
      .join(" ");
    if (!pts) return null;
    return { xMin, xMax, sx, sy, pts };
  }, [xs, ys]);

  if (!geom)
    return (
      <div className="rounded-lg bg-slate-50 px-3 py-6 text-center text-xs text-steel">
        Nessun dato di curva da mostrare.
      </div>
    );

  const yTicks = [0, 0.25, 0.5, 0.75, 1];
  const xTicks = [400, 450, 500, 550, 600, 650, 700].filter(
    (t) => t >= geom.xMin && t <= geom.xMax
  );

  return (
    <svg
      viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
      className="h-auto w-full"
      role="img"
      aria-label="Curva di riflettanza stimata"
      preserveAspectRatio="xMidYMid meet"
    >
      {/* y gridlines + labels */}
      {yTicks.map((t) => {
        const y = geom.sy(t);
        return (
          <g key={`y${t}`}>
            <line
              x1={PAD.left}
              x2={PAD.left + PLOT_W}
              y1={y}
              y2={y}
              className="stroke-slate-200"
              strokeWidth={1}
            />
            <text
              x={PAD.left - 8}
              y={y + 4}
              textAnchor="end"
              className="fill-steel"
              fontSize={11}
            >
              {t.toFixed(2)}
            </text>
          </g>
        );
      })}

      {/* x ticks + labels */}
      {xTicks.map((t) => {
        const x = geom.sx(t);
        return (
          <g key={`x${t}`}>
            <line
              x1={x}
              x2={x}
              y1={PAD.top + PLOT_H}
              y2={PAD.top + PLOT_H + 4}
              className="stroke-slate-300"
              strokeWidth={1}
            />
            <text
              x={x}
              y={PAD.top + PLOT_H + 18}
              textAnchor="middle"
              className="fill-steel"
              fontSize={11}
            >
              {t}
            </text>
          </g>
        );
      })}

      {/* axes */}
      <line
        x1={PAD.left}
        x2={PAD.left}
        y1={PAD.top}
        y2={PAD.top + PLOT_H}
        className="stroke-slate-400"
        strokeWidth={1}
      />
      <line
        x1={PAD.left}
        x2={PAD.left + PLOT_W}
        y1={PAD.top + PLOT_H}
        y2={PAD.top + PLOT_H}
        className="stroke-slate-400"
        strokeWidth={1}
      />

      {/* axis titles */}
      <text
        x={PAD.left + PLOT_W / 2}
        y={VIEW_H - 4}
        textAnchor="middle"
        className="fill-steel"
        fontSize={11}
      >
        lunghezza d'onda (nm)
      </text>
      <text
        x={14}
        y={PAD.top + PLOT_H / 2}
        textAnchor="middle"
        transform={`rotate(-90 14 ${PAD.top + PLOT_H / 2})`}
        className="fill-steel"
        fontSize={11}
      >
        riflettanza (0–1)
      </text>

      {/* the estimated curve */}
      <polyline
        points={geom.pts}
        fill="none"
        className="stroke-brand-600"
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

function MetamerismPreview({ estimate }: { estimate: ReflectanceEstimate }) {
  const [illuminant, setIlluminant] = useState<Illuminant>(
    (ILLUMINANTS as string[]).includes(estimate.illuminant)
      ? (estimate.illuminant as Illuminant)
      : "D65"
  );

  const render = useMutation({
    mutationFn: (ill: Illuminant) =>
      renderUnder({ reflectance: estimate.reflectance, illuminant: ill, observer: estimate.observer }),
  });

  const data = render.data;
  const swatch =
    data && data.srgb.length >= 3
      ? `rgb(${Math.round(data.srgb[0])}, ${Math.round(data.srgb[1])}, ${Math.round(data.srgb[2])})`
      : undefined;

  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <div className="mb-2 text-xs font-medium uppercase tracking-wide text-steel">
        Verifica metamerismo (stimata)
      </div>
      <p className="mb-2 text-xs text-steel">
        Stima dell'aspetto della curva sotto una luce diversa. È un calcolo, non una misura: serve
        solo a evidenziare un possibile metamerismo.
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <div className="inline-flex overflow-hidden rounded-lg border border-slate-300">
          {ILLUMINANTS.map((ill) => (
            <button
              key={ill}
              type="button"
              onClick={() => {
                setIlluminant(ill);
                render.mutate(ill);
              }}
              className={`min-h-[44px] px-4 text-sm font-medium transition ${
                illuminant === ill ? "bg-brand-600 text-white" : "bg-white text-steel hover:bg-slate-50"
              }`}
            >
              {ill}
            </button>
          ))}
        </div>
        <Button
          variant="ghost"
          loading={render.isPending}
          onClick={() => render.mutate(illuminant)}
        >
          Calcola anteprima
        </Button>
      </div>

      {data && (
        <div className="mt-3 flex items-center gap-3">
          <span
            className="h-12 w-12 shrink-0 rounded-lg border border-slate-300"
            style={swatch ? { backgroundColor: swatch } : undefined}
            aria-label="anteprima colore stimata"
          />
          <div className="text-sm">
            <div className="font-medium text-ink">
              Anteprima sotto luce {data.illuminant} (STIMATA)
            </div>
            <div className="text-xs text-steel">{fmtLab(data.lab)}</div>
            {swatch && <div className="text-[11px] text-slate-400">{swatch}</div>}
          </div>
        </div>
      )}
      <ErrorText error={render.error} />
    </div>
  );
}

export function SpectralCurveViewer({
  estimate,
  title,
}: {
  estimate: ReflectanceEstimate;
  title?: string;
}) {
  const confidencePct = Math.round((estimate.confidence ?? 0) * 100);

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          {title && <span className="font-medium text-ink">{title}</span>}
          <Badge kind="warn">STIMATA · R&D</Badge>
          {estimate.in_gamut === false && <Badge kind="warn">fuori gamut</Badge>}
        </div>
        <span className="text-xs text-steel">
          {estimate.illuminant} · {estimate.observer}
        </span>
      </div>

      {/* honesty banner — the disclaimer text comes from the backend */}
      <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-xs leading-relaxed text-amber-800">
        <div className="font-semibold">Stima — non è una misura</div>
        <p className="mt-1">{estimate.disclaimer}</p>
        <p className="mt-1">
          La ricostruzione RGB→spettro è sotto-determinata (metamerismo): la curva è indicativa e{" "}
          <b>non viene inclusa nel report sigillato</b>.
        </p>
      </div>

      <ReflectanceChart estimate={estimate} />

      <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        <div
          className="rounded-lg bg-slate-50 px-3 py-2"
          title="Euristica NON validata: misura quanto la curva richiude sul colore misurato (ΔE round-trip), non l'accuratezza spettrale. Non esiste uno spettro 'vero' da confrontare."
        >
          <div className="text-[11px] uppercase tracking-wide text-steel">
            Fedeltà colore (euristica)
          </div>
          <div className="font-semibold text-ink">{confidencePct}%</div>
        </div>
        <div
          className="rounded-lg bg-slate-50 px-3 py-2"
          title="Differenza di colore (CIEDE2000) fra il colore misurato e quello ricalcolato dalla curva stimata: vicino a 0 = la curva riproduce il colore."
        >
          <div className="text-[11px] uppercase tracking-wide text-steel">ΔE round-trip</div>
          <div className="font-semibold text-ink">{estimate.roundtrip_delta_e.toFixed(2)}</div>
        </div>
        <div className="rounded-lg bg-slate-50 px-3 py-2 col-span-2">
          <div className="text-[11px] uppercase tracking-wide text-steel">Metodo</div>
          <div className="truncate font-medium text-ink" title={`${estimate.method} · ${estimate.engine}`}>
            {estimate.method} · {estimate.engine}
          </div>
        </div>
      </div>

      <div className="text-xs text-steel">
        Lab in ingresso: {fmtLab(estimate.input_lab)} → round-trip: {fmtLab(estimate.roundtrip_lab)}
      </div>

      {estimate.warnings.length > 0 && (
        <div className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
          ⚠ {estimate.warnings.join(" · ")}
        </div>
      )}

      <MetamerismPreview estimate={estimate} />
    </div>
  );
}
