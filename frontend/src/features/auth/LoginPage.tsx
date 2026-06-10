import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import type { CompanyBrief } from "@/api/types";
import { Button, ErrorText, Field, Spinner, TextInput } from "@/components/ui";
import { useAuth } from "@/lib/auth";

export function LoginPage() {
  const { login, selectCompany } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [companies, setCompanies] = useState<CompanyBrief[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function onLogin(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await login(email, password);
      if (res.company_id) navigate("/");
      else if (res.companies.length > 0) setCompanies(res.companies);
      else setError(new Error("Nessuna azienda associata a questo account."));
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  async function pick(id: string) {
    setBusy(true);
    try {
      await selectCompany(id);
      navigate("/");
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-brand-50 to-slate-100 p-4">
      <div className="mb-6 flex flex-col items-center gap-2 text-center">
        <span className="grid h-12 w-12 place-items-center rounded-2xl bg-brand-600 text-lg font-bold text-white shadow-card">
          S
        </span>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">Solidità 4.0</h1>
        <p className="text-sm text-steel">Controllo qualità tessile digitale</p>
      </div>

      <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
        {companies ? (
          <div className="space-y-2">
            <p className="text-sm font-medium text-steel">Scegli l'azienda</p>
            {companies.map((c) => (
              <button
                key={c.id}
                disabled={busy}
                onClick={() => pick(c.id)}
                className="flex w-full items-center justify-between rounded-lg border border-slate-200 px-3 py-3 text-sm hover:border-brand-500 hover:bg-brand-50"
              >
                <span className="font-medium">{c.name}</span>
                <span className="text-xs uppercase text-steel">{c.role}</span>
              </button>
            ))}
            <ErrorText error={error} />
          </div>
        ) : (
          <form onSubmit={onLogin} className="space-y-4">
            <Field label="Email">
              <TextInput
                type="email"
                inputMode="email"
                autoComplete="username"
                placeholder="nome@azienda.it"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Field>
            <Field label="Password">
              <TextInput
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field>
            <ErrorText error={error} />
            <Button type="submit" disabled={busy} className="w-full">
              {busy ? <Spinner /> : "Accedi"}
            </Button>
          </form>
        )}
      </div>

      <p className="mt-6 max-w-sm text-center text-[11px] text-slate-400">
        Piattaforma di tracciabilità e pre-validazione. Non sostituisce un laboratorio
        accreditato.
      </p>
    </main>
  );
}
