import { useMutation, useQuery } from "@tanstack/react-query";

import { createCheckout, listSubscriptions } from "@/api/quality";
import { Badge, Button, Card, ErrorText, PageHeader } from "@/components/ui";

const PLANS: { id: "trace" | "vision"; name: string; blurb: string }[] = [
  { id: "trace", name: "Trace", blurb: "Capitolati, batch zero, prove, report con sigillo, ledger." },
  { id: "vision", name: "Vision Pro", blurb: "Tutto Trace + analisi immagine multifibra, tarature, validazione." },
];

export function BillingPage() {
  const subs = useQuery({ queryKey: ["subscriptions"], queryFn: listSubscriptions });
  const current = subs.data?.[0];

  const checkout = useMutation({
    mutationFn: (plan: "trace" | "vision") => createCheckout(plan),
    onSuccess: (r) => {
      window.location.href = r.url; // redirect to Stripe Checkout
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Abbonamento" subtitle="Piano e fatturazione (Stripe)" />

      <Card>
        <div className="mb-2 font-medium">Piano attuale</div>
        {subs.isLoading ? (
          <p className="text-steel">Caricamento…</p>
        ) : current ? (
          <div className="flex items-center gap-2 text-sm">
            <Badge kind={current.status === "active" ? "pass" : "warn"}>{current.status}</Badge>
            <span className="font-medium capitalize">{current.plan}</span>
            {current.current_period_end && (
              <span className="text-steel">
                · rinnovo {new Date(current.current_period_end).toLocaleDateString()}
              </span>
            )}
          </div>
        ) : (
          <p className="text-sm text-steel">Nessun abbonamento attivo.</p>
        )}
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        {PLANS.map((p) => (
          <Card key={p.id}>
            <div className="font-medium">{p.name}</div>
            <p className="mt-1 text-sm text-steel">{p.blurb}</p>
            <div className="mt-3">
              <Button disabled={checkout.isPending} onClick={() => checkout.mutate(p.id)}>
                {checkout.isPending ? "…" : `Attiva ${p.name}`}
              </Button>
            </div>
          </Card>
        ))}
      </div>
      <ErrorText error={checkout.error} />
      <p className="text-xs text-steel">
        Il pagamento avviene su Stripe (checkout sicuro). L'abbonamento attiva il piano e i
        relativi moduli. Disponibile quando Stripe è configurato.
      </p>
    </div>
  );
}
