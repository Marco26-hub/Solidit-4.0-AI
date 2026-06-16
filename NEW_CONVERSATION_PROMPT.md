# Prompt per nuova conversazione — Solidità 4.0

Copia e incolla questo come primo messaggio in una nuova sessione Claude Code
aperta nella cartella del progetto.

---

Lavori su **Solidità 4.0**, SaaS di controllo qualità tessile + **sistema di
imaging digitale validabile** per la valutazione assistita della solidità colore
(textile + cuoio). Repo GitHub: `https://github.com/Marco26-hub/Solidit-4.0-AI`
(origin/main). Obiettivo triplo: **App Store**, **accreditamento del metodo
(Accredia/ISO 17025)**, **vendita**.

**Prima di tutto leggi**, in ordine: `CLAUDE.md` (regole non negoziabili),
`HANDOFF.md` (stato completo), `DEPLOY.md`, e le migrazioni in
`backend/app/db/migrations/versions/` (lo schema racconta il dominio). C'è anche
una memoria di build in `~/.claude/.../memory/solidita-build-state.md`.

**Stato (già fatto, 65 test backend verdi, tutto pushato):** multi-tenant RLS,
auth JWT rotation, capitolati brand+pass/fail, batch zero, articoli+varianti,
catalogo norme UNI EN ISO 105 / AATCC / ASTM / cuoio (ISO+IULTCS) con menu
raggruppato, upload norma licenziata per-tenant. Vision engine `vision-core-0.2.x`:
auto-detect striscia + bande in ordine, RGB→Lab→ΔE CIEDE2000, profili grading
configurabili per norma (builtin = ESEMPIO, flaggati), scala grigia in-frame +
**correzione colore ancorata a Lab certificato** della piastrina, colour-change
vs variante, ripetibilità su repliche, strict-mode (rifiuto cattura scarsa),
quality gate. Tarature: `calibration_references` con scadenza che **blocca
l'analisi**. Report: PDF + SHA-256 + ledger + **finalize/lock** + provenienza
piena + **verifica pubblica** (QR → `/verify/:id?h=`). Validazione: modulo
campagne + statistiche + **report PDF di validazione** + **checklist
accreditabilità auto-aggiornante** (`/accreditation/readiness`). Fascicolo+8 SOP
in `docs/quality/`. App mobile: scaffold cattura nativa (vision-camera) + login.
Deploy: `Dockerfile.prod`, `render.yaml`, `infra/neon/setup_neon.sh`, storage S3/R2.

**Regole non negoziabili:** RLS multi-tenant (ruolo DB non-superuser); niente
formule/tabelle ISO/AATCC proprietarie hardcoded (mapping configurabile, profili
ESEMPIO da sostituire con validati); SHA-256 = sigillo integrità, MAI firma
qualificata; geometria e correzione colore separate; iPhone = quality gate, non
metrologia da solo (serve kit); ogni fallback non validato va FLAGGATO nel
risultato e nel PDF; posizionamento: "pre-valutazione assistita", non
"spettrofotometro" né "sostituto di laboratorio accreditato". Non riprodurre
testo protetto delle norme: solo identificativi + titoli originali.

**Onestà accreditamento:** il software prepara/documenta validazione + readiness,
ma l'accreditamento lo concede Accredia (lab conforme + consulente 17025 + metodo
nello scopo). Mai dichiarare il software "accreditato" da solo.

**Setup locale:** Postgres 16 con ruolo `solidita_app` (`infra/postgres/init.sql`);
`cd backend && pip install -e ".[vision]" && python -m alembic upgrade head &&
uvicorn app.main:app --port 8000`; `cd frontend && npm i && npm run dev`;
`pytest backend` (65 verdi, serve Postgres). **Riavvia uvicorn dopo modifiche
backend.** Verifica le modifiche frontend via i tool preview.

**Prossimo lavoro (in ordine, vedi HANDOFF "Cosa resta"):**
1. **Deploy live** — **Neon già pronto** (schema migrato a 0015, ruolo
   `solidita_app`, RLS ok). `DATABASE_URL` backend = endpoint **diretto** (non
   `-pooler`) + `?sslmode=require` SENZA `channel_binding`. Resta: bucket R2/S3
   (env `S3_*`), backend su **Render** (`render.yaml`), frontend su **Vercel**
   (root=`frontend`, `VITE_API_BASE`). ⚠️ la password DB è stata condivisa in chat
   → **resettarla in Neon** prima della prod (Roles → Reset).
2. Completare **app iOS nativa** (frame-processor blur/esposizione reale, marker
   ArUco) → Apple Developer + icona/screenshot + TestFlight + submit (no IAP).
3. Hardening vision: ArUco + omografia (OpenCV), worker async per vision/PDF/email.

Billing Stripe: codice pronto (checkout/webhook/gating + pagina) — resta solo
configurare account Stripe + price IDs in env.

**Bloccanti non-codice (utente/business):** campioni reali + spettrofotometro per
la validazione, kit hardware certificato, consulente ISO 17025, profili grading
validati/licenziati.

**Come lavorare:** lavora a piccoli incrementi verificati (test backend + build
frontend + verifica live), committa e pusha ogni milestone con messaggi chiari.
Chiedi conferma solo per scelte che cambiano la direzione o per credenziali/azioni
esterne. Stile risposte: italiano, conciso.

Per cominciare: leggi `HANDOFF.md` e dimmi da quale punto di "Cosa resta" partiamo.
