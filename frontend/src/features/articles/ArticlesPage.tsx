import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { addVariant, createArticle, listArticles, listGradingProfiles } from "@/api/quality";
import type { Article, LabValue } from "@/api/types";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorText,
  Field,
  Hint,
  PageHeader,
  TextInput,
} from "@/components/ui";

type LabCell = { L: string; a: string; b: string };

function parseLab(c: LabCell): LabValue | null {
  if (c.L === "" || c.a === "" || c.b === "") return null;
  return { L: Number(c.L), a: Number(c.a), b: Number(c.b) };
}

export function ArticlesPage() {
  const qc = useQueryClient();
  const articles = useQuery({ queryKey: ["articles"], queryFn: listArticles });
  const profiles = useQuery({ queryKey: ["grading-profiles"], queryFn: () => listGradingProfiles() });

  // new-article form
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [composition, setComposition] = useState("");
  const [vCode, setVCode] = useState("");
  const [vColor, setVColor] = useState("");
  const [vLot, setVLot] = useState("");
  const [vLab, setVLab] = useState<LabCell>({ L: "", a: "", b: "" });

  const create = useMutation({
    mutationFn: () => {
      const lab = parseLab(vLab);
      const variants = vCode
        ? [{ code: vCode, color_name: vColor || null, lot_code: vLot || null, reference_lab: lab }]
        : [];
      return createArticle({
        code,
        name: name || null,
        composition: composition || null,
        variants,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["articles"] });
      setCode("");
      setName("");
      setComposition("");
      setVCode("");
      setVColor("");
      setVLot("");
      setVLab({ L: "", a: "", b: "" });
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Articoli & Varianti"
        subtitle="Campione di produzione (tintoria/stamperia). Ogni variante (colore/lotto) tiene il Lab di riferimento per la solidità del colore (colour-change)."
      />

      <Card className="border-brand-200 bg-brand-50">
        <p className="text-sm text-steel">
          <b>Passo 1:</b> registra l'articolo e le sue varianti (con il Lab di riferimento). Poi crea
          la striscia in <b>Batch Zero</b> e potrai avviare una <b>Prova</b>.
        </p>
      </Card>

      <Card>
        <div className="mb-2 font-medium">Articoli</div>
        <ErrorText error={articles.error} />
        <div className="space-y-3">
          {(articles.data ?? []).map((a) => (
            <ArticleRow key={a.id} article={a} />
          ))}
          {articles.data?.length === 0 && (
            <EmptyState
              title="Nessun articolo"
              hint="Crea il primo articolo di produzione con le sue varianti qui sotto."
            />
          )}
        </div>
      </Card>

      <Card>
        <div className="mb-3 font-medium">Nuovo articolo</div>
        <div className="grid gap-3 sm:grid-cols-3">
          <Field label="Codice articolo" required>
            <TextInput value={code} onChange={(e) => setCode(e.target.value)} placeholder="ART-100" />
          </Field>
          <Field label="Nome">
            <TextInput value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
          <Field label="Composizione">
            <TextInput
              value={composition}
              onChange={(e) => setComposition(e.target.value)}
              placeholder="95% CO 5% EA"
            />
          </Field>
        </div>

        <div className="mt-4 text-sm font-medium">Prima variante (opzionale)</div>
        <p className="text-xs text-steel">
          Il Lab di riferimento è il colore del campione non trattato — serve al confronto
          colour-change.
        </p>
        <div className="mt-2 grid gap-3 sm:grid-cols-3">
          <Field label="Codice variante">
            <TextInput value={vCode} onChange={(e) => setVCode(e.target.value)} placeholder="RED" />
          </Field>
          <Field label="Colore">
            <TextInput value={vColor} onChange={(e) => setVColor(e.target.value)} />
          </Field>
          <Field label="Lotto">
            <TextInput value={vLot} onChange={(e) => setVLot(e.target.value)} />
          </Field>
        </div>
        <div className="mt-2 grid grid-cols-3 gap-2">
          {(["L", "a", "b"] as const).map((k) => (
            <Field key={k} label={`Rif. ${k}`}>
              <TextInput
                type="number"
                step="0.1"
                value={vLab[k]}
                onChange={(e) => setVLab((s) => ({ ...s, [k]: e.target.value }))}
              />
            </Field>
          ))}
        </div>

        <div className="mt-3">
          <Button type="button" loading={create.isPending} disabled={!code} onClick={() => create.mutate()}>
            Crea articolo
          </Button>
          {!code && <Hint>Inserisci il codice articolo per salvare.</Hint>}
        </div>
        <ErrorText error={create.error} />
      </Card>

      <Card>
        <div className="mb-2 font-medium">Profili di grading (ΔE → grado)</div>
        <p className="mb-3 text-xs text-steel">
          Mappatura configurabile per norma (UNI EN ISO / AATCC / ASTM) e tipo di valutazione. I
          profili builtin usano soglie ESEMPIO — da validare/licenziare per azienda.
        </p>
        <ErrorText error={profiles.error} />
        <div className="overflow-x-auto">
          <table className="w-full min-w-[420px] text-sm">
            <thead className="text-left text-steel">
              <tr>
                <th className="py-1">Norma</th>
                <th>Tipo</th>
                <th>Codice</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {(profiles.data ?? []).map((p) => (
                <tr key={p.id} className="border-t">
                  <td className="py-1.5">{p.standard_family}</td>
                  <td>{p.assessment_type === "change" ? "colour-change" : "staining"}</td>
                  <td className="text-xs text-steel">{p.code}</td>
                  <td className="text-right">
                    {p.is_builtin ? (
                      <Badge kind="muted">builtin · esempio</Badge>
                    ) : (
                      <Badge kind="pass">custom</Badge>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function ArticleRow({ article }: { article: Article }) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [vCode, setVCode] = useState("");
  const [vColor, setVColor] = useState("");
  const [vLot, setVLot] = useState("");
  const [vLab, setVLab] = useState<LabCell>({ L: "", a: "", b: "" });

  const add = useMutation({
    mutationFn: () =>
      addVariant(article.id, {
        code: vCode,
        color_name: vColor || null,
        lot_code: vLot || null,
        reference_lab: parseLab(vLab),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["articles"] });
      setVCode("");
      setVColor("");
      setVLot("");
      setVLab({ L: "", a: "", b: "" });
    },
  });

  return (
    <div className="rounded-lg border border-slate-200">
      <button
        type="button"
        className="flex w-full items-center justify-between px-3 py-2 text-left"
        onClick={() => setOpen((o) => !o)}
      >
        <div>
          <div className="font-medium">
            {article.code}
            {article.name ? ` · ${article.name}` : ""}
          </div>
          <div className="text-xs text-steel">
            {article.composition ?? "—"} · {article.variants.length} varianti
          </div>
        </div>
        <span className="text-xs text-steel">{open ? "chiudi" : "apri"}</span>
      </button>

      {open && (
        <div className="border-t px-3 py-3">
          <div className="space-y-1">
            {article.variants.map((v) => (
              <div key={v.id} className="flex items-center justify-between text-sm">
                <span>
                  <b>{v.code}</b>
                  {v.color_name ? ` · ${v.color_name}` : ""}
                  {v.lot_code ? ` · lotto ${v.lot_code}` : ""}
                </span>
                {v.reference_lab ? (
                  <span className="text-xs text-steel">
                    L {v.reference_lab.L} · a {v.reference_lab.a} · b {v.reference_lab.b}
                  </span>
                ) : (
                  <Badge kind="warn">no Lab rif.</Badge>
                )}
              </div>
            ))}
            {article.variants.length === 0 && (
              <p className="text-sm text-steel">Nessuna variante.</p>
            )}
          </div>

          <div className="mt-3 text-sm font-medium">Aggiungi variante</div>
          <div className="mt-1 grid gap-2 sm:grid-cols-3">
            <TextInput placeholder="codice" value={vCode} onChange={(e) => setVCode(e.target.value)} />
            <TextInput placeholder="colore" value={vColor} onChange={(e) => setVColor(e.target.value)} />
            <TextInput placeholder="lotto" value={vLot} onChange={(e) => setVLot(e.target.value)} />
          </div>
          <div className="mt-2 grid grid-cols-3 gap-2">
            {(["L", "a", "b"] as const).map((k) => (
              <TextInput
                key={k}
                type="number"
                step="0.1"
                placeholder={`rif. ${k}`}
                value={vLab[k]}
                onChange={(e) => setVLab((s) => ({ ...s, [k]: e.target.value }))}
              />
            ))}
          </div>
          <div className="mt-2">
            <Button disabled={!vCode || add.isPending} onClick={() => add.mutate()}>
              {add.isPending ? "…" : "Aggiungi variante"}
            </Button>
          </div>
          <ErrorText error={add.error} />
        </div>
      )}
    </div>
  );
}
