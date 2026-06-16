import { useEffect, useState } from "react";

import { publicVerifyReport, type PublicVerify } from "@/api/quality";

/**
 * Public, unauthenticated report verification. The report PDF's QR code points
 * here: /verify/:id?h=<sha256>. Shows whether the integrity seal holds — no login.
 */
export function VerifyPage() {
  const [state, setState] = useState<"loading" | "done" | "error">("loading");
  const [result, setResult] = useState<PublicVerify | null>(null);

  useEffect(() => {
    const parts = window.location.pathname.split("/");
    const id = parts[parts.indexOf("verify") + 1];
    const hash = new URLSearchParams(window.location.search).get("h") ?? "";
    if (!id || !hash) {
      setState("error");
      return;
    }
    publicVerifyReport(id, hash)
      .then((r) => {
        setResult(r);
        setState("done");
      })
      .catch((e) => {
        console.error("VerifyPage: report verification failed", e);
        setState("error");
      });
  }, []);

  const valid = result?.valid === true;

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
        <div className="mb-4 flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-sm font-bold text-white">
            S
          </span>
          <div className="text-sm font-semibold">Solidità 4.0 — Verifica report</div>
        </div>

        {state === "loading" && <p className="text-steel">Verifica in corso…</p>}
        {state === "error" && (
          <p className="text-red-600">Link non valido o report non verificabile.</p>
        )}

        {state === "done" && (
          <>
            <div
              className={`rounded-xl px-4 py-5 text-center ${
                valid ? "bg-emerald-50" : "bg-red-50"
              }`}
            >
              <div className={`text-3xl ${valid ? "text-emerald-600" : "text-red-600"}`}>
                {valid ? "✓" : "✕"}
              </div>
              <div
                className={`mt-1 text-lg font-semibold ${
                  valid ? "text-emerald-700" : "text-red-700"
                }`}
              >
                {valid ? "Report autentico" : "Report NON verificato"}
              </div>
              <div className="mt-1 text-xs text-steel">
                {valid
                  ? "Il sigillo di integrità SHA-256 corrisponde."
                  : "Sigillo non corrispondente o report inesistente."}
              </div>
            </div>

            {valid && (
              <dl className="mt-4 space-y-2 text-sm">
                <Row k="Numero report" v={result?.report_number} />
                <Row k="Azienda" v={result?.company_name} />
                <Row
                  k="Emesso il"
                  v={result?.issued_at ? new Date(result.issued_at).toLocaleString() : null}
                />
                <Row k="Stato" v={result?.locked ? "ufficiale (bloccato)" : "generato"} />
                <Row k="SHA-256" v={result?.sha256_hash?.slice(0, 24) + "…"} mono />
              </dl>
            )}

            <p className="mt-5 text-[11px] text-slate-400">
              Sigillo tecnico di integrità (SHA-256), non firma digitale qualificata. Sistema di
              imaging digitale per pre-valutazione: non sostituisce un laboratorio accreditato.
            </p>
          </>
        )}
      </div>
    </div>
  );
}

function Row({ k, v, mono }: { k: string; v?: string | null; mono?: boolean }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-steel">{k}</dt>
      <dd className={`text-right ${mono ? "font-mono text-xs" : ""}`}>{v ?? "—"}</dd>
    </div>
  );
}
