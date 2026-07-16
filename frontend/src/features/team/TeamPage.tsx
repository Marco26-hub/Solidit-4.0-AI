import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addAuthorization,
  addMember,
  listAuthorizations,
  listMembers,
  removeMember,
  revokeAuthorization,
} from "@/api/team";
import { listTestMethods } from "@/api/quality";
import { MethodSelect } from "@/components/MethodSelect";
import { PageGuide } from "@/components/PageGuide";
import { roleLabel, useRole, type Role } from "@/lib/roles";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorText,
  Field,
  Hint,
  PageHeader,
  Select,
  TextInput,
} from "@/components/ui";

// Team management: the admin creates operator/manager accounts so the
// operator→approval flow (ISO 17025 §6.2 personnel identification) is real.

const ROLE_BADGE: Record<string, "pass" | "warn" | "muted"> = {
  company_admin: "pass",
  lab_manager: "warn",
  operator: "muted",
};

export function TeamPage() {
  const qc = useQueryClient();
  const { canAdmin } = useRole();
  const members = useQuery({ queryKey: ["members"], queryFn: listMembers });

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<Role>("operator");

  const add = useMutation({
    mutationFn: () =>
      addMember({ email, password, full_name: fullName || null, role }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["members"] });
      setEmail("");
      setPassword("");
      setFullName("");
      setRole("operator");
    },
  });

  const remove = useMutation({
    mutationFn: (userId: string) => removeMember(userId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["members"] }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Team"
        subtitle="Account e ruoli: l'operatore esegue, il responsabile approva"
      />
      <PageGuide
        defaultOpen={(members.data?.length ?? 0) <= 1}
        steps={[
          <>Crea un account per ogni persona del laboratorio: ogni risultato resta legato a chi l'ha fatto (richiesto in ottica ISO 17025).</>,
          <><b>Operatore</b> = esegue prove, foto e risultati. <b>Manager</b> = come l'operatore, più approva/finalizza i report e gestisce capitolati, batch e tarature. <b>Amministratore</b> = tutto, più il team.</>,
          <>Consegna la password temporanea alla persona: al primo accesso la può cambiare dal profilo.</>,
          <>Rimuovere un membro gli toglie subito l'accesso ai dati dell'azienda (i suoi risultati storici restano tracciati).</>,
        ]}
      />

      {canAdmin && (
        <Card>
          <div className="mb-3 font-medium">Aggiungi membro</div>
          <div className="grid gap-3 md:grid-cols-4">
            <Field label="Email">
              <TextInput
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="nome@azienda.it"
              />
            </Field>
            <Field label="Password temporanea (min 8)">
              <TextInput
                type="text"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="da consegnare alla persona"
              />
            </Field>
            <Field label="Nome (opzionale)">
              <TextInput value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </Field>
            <Field label="Ruolo">
              <Select value={role} onChange={(e) => setRole(e.target.value as Role)}>
                <option value="operator">Operatore — esegue prove e risultati</option>
                <option value="lab_manager">Manager — approva report e configura</option>
                <option value="company_admin">Amministratore — tutto + team</option>
              </Select>
            </Field>
          </div>
          <div className="mt-3">
            <Button
              type="button"
              loading={add.isPending}
              disabled={!email || password.length < 8}
              onClick={() => add.mutate()}
            >
              Crea account
            </Button>
            {password.length > 0 && password.length < 8 && (
              <Hint>La password deve avere almeno 8 caratteri.</Hint>
            )}
          </div>
          <ErrorText error={add.error} />
        </Card>
      )}

      <Card>
        <div className="mb-2 font-medium">Membri</div>
        <ErrorText error={members.error || remove.error} />
        {(members.data?.length ?? 0) === 0 ? (
          <EmptyState title="Nessun membro" hint="Aggiungi il primo account del team." />
        ) : (
          <div className="divide-y">
            {(members.data ?? []).map((m) => (
              <div key={m.user_id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                <div className="min-w-0">
                  <div className="text-sm font-medium">{m.full_name || m.email}</div>
                  <div className="text-xs text-steel">
                    {m.email} · dal {new Date(m.created_at).toLocaleDateString("it-IT")}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge kind={ROLE_BADGE[m.role] ?? "muted"}>{roleLabel(m.role)}</Badge>
                  {canAdmin && (
                    <Button
                      variant="ghost"
                      loading={remove.isPending}
                      onClick={() => {
                        if (
                          window.confirm(
                            `Rimuovere ${m.email} dal team?\n\nPerderà subito l'accesso ai dati dell'azienda.`
                          )
                        )
                          remove.mutate(m.user_id);
                      }}
                    >
                      Rimuovi
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <AuthorizationsCard />
    </div>
  );
}

// ── Registro autorizzazioni operatori (ISO 17025 §6.2) ───────────────────────

function AuthorizationsCard() {
  const qc = useQueryClient();
  const { canManage } = useRole();
  const members = useQuery({ queryKey: ["members"], queryFn: listMembers });
  const methods = useQuery({ queryKey: ["test-methods"], queryFn: listTestMethods });
  const auths = useQuery({ queryKey: ["authorizations"], queryFn: listAuthorizations });

  const [userId, setUserId] = useState("");
  const [methodCode, setMethodCode] = useState("");
  const [validUntil, setValidUntil] = useState("");
  const [notes, setNotes] = useState("");

  const add = useMutation({
    mutationFn: () =>
      addAuthorization({
        user_id: userId,
        method_code: methodCode || null,
        valid_until: validUntil || null,
        training_notes: notes || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["authorizations"] });
      setMethodCode("");
      setValidUntil("");
      setNotes("");
    },
  });
  const revoke = useMutation({
    mutationFn: (id: string) => revokeAuthorization(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["authorizations"] }),
  });

  return (
    <Card>
      <div className="mb-1 font-medium">Registro autorizzazioni operatori (ISO 17025 §6.2)</div>
      <p className="mb-3 text-xs text-steel">
        Chi è autorizzato a eseguire quale metodo, da quando e con quale formazione. Ogni risultato
        registra l'operatore e se era autorizzato; l'esito compare anche nel PDF del report.
      </p>

      {canManage && (
        <div className="mb-4 grid gap-3 md:grid-cols-4">
          <Field label="Membro">
            <Select value={userId} onChange={(e) => setUserId(e.target.value)}>
              <option value="">— scegli —</option>
              {(members.data ?? []).map((m) => (
                <option key={m.user_id} value={m.user_id}>
                  {m.full_name || m.email}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Metodo (vuoto = tutti)">
            <MethodSelect
              methods={methods.data ?? []}
              value={methodCode}
              onChange={setMethodCode}
              emptyLabel="Tutti i metodi"
            />
          </Field>
          <Field label="Scadenza (opzionale)">
            <TextInput
              type="date"
              value={validUntil}
              onChange={(e) => setValidUntil(e.target.value)}
            />
          </Field>
          <Field label="Formazione / evidenza">
            <TextInput
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="es. corso interno 07/2026"
            />
          </Field>
          <div className="md:col-span-4">
            <Button
              type="button"
              loading={add.isPending}
              disabled={!userId}
              onClick={() => add.mutate()}
            >
              Registra autorizzazione
            </Button>
          </div>
        </div>
      )}
      <ErrorText error={add.error || revoke.error || auths.error} />

      {(auths.data?.length ?? 0) === 0 ? (
        <EmptyState
          title="Nessuna autorizzazione registrata"
          hint="Registra chi può eseguire quali metodi: serve per l'accreditamento."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[520px] text-sm">
            <thead className="text-left text-steel">
              <tr>
                <th className="py-1">Operatore</th>
                <th>Metodo</th>
                <th>Validità</th>
                <th>Stato</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {(auths.data ?? []).map((a) => (
                <tr key={a.id} className="border-t">
                  <td className="py-1.5">{a.email}</td>
                  <td>{a.method_code ?? "tutti i metodi"}</td>
                  <td className="text-xs text-steel">
                    dal {new Date(a.valid_from).toLocaleDateString("it-IT")}
                    {a.valid_until
                      ? ` al ${new Date(a.valid_until).toLocaleDateString("it-IT")}`
                      : " · senza scadenza"}
                  </td>
                  <td>
                    <Badge kind={a.status === "active" ? "pass" : "muted"}>
                      {a.status === "active" ? "attiva" : "revocata"}
                    </Badge>
                  </td>
                  <td className="text-right">
                    {canManage && a.status === "active" && (
                      <Button
                        variant="ghost"
                        loading={revoke.isPending}
                        onClick={() => {
                          if (window.confirm(`Revocare l'autorizzazione di ${a.email}?`))
                            revoke.mutate(a.id);
                        }}
                      >
                        Revoca
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
