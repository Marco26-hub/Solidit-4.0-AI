# HANDOFF.md — Solidità 4.0 Project Handoff

> Aggiornato: 2026-06-11 · Repo: https://github.com/Marco26-hub/Solidit-4.0-AI

## Contesto

Solidità 4.0 è un SaaS industriale per il controllo qualità tessile (tintorie,
stamperie, finissaggi, brand moda): digitalizza prove di solidità colore, report,
batch zero, capitolati brand e storico metrologico.

Posizionamento corretto: **sistema di digital imaging validabile per la
valutazione assistita / pre-valutazione della solidità colore**. NON comunicare
come sostituto di un laboratorio accreditato né come "spettrofotometro".

## Stato attuale — CODEBASE FUNZIONANTE

Monorepo attivo: `backend/` (FastAPI, Python 3.12) · `frontend/` (React+Vite+TS)
· `mobile/` (skeleton RN) · `infra/` (docker-compose Postgres 16 + Redis).

**62 test backend verdi · ruff pulito · build frontend pulito.**

### Implementato (Trace + Vision base + fondamenta accreditamento)

- **Multi-tenant**: PostgreSQL RLS (FORCE, ruolo app non-superuser `solidita_app`,
  `SET LOCAL` per transazione), JWT access/refresh con rotation + reuse detection,
  rate limiting, security headers, audit log **append-only** (REVOKE UPDATE/DELETE).
- **Dominio qualità**: brand specs/capitolato (CSV import + PDF allegato), batch
  zero multifibra con profili striscia per norma (ISO 105-F10 DW/TV, AATCC No.1/10),
  test methods catalogo UNI EN ISO 105 (E01-E08 acqua/mare/clorata/sudore 37°C,
  C08/C10, D01, B02, N01, P01, X11/X12) + AATCC + ASTM, articoli+varianti
  (riferimento colour-change), test jobs multi-solidità, risultato manuale con
  fibre precaricate dalla norma.
- **Vision engine** (`vision-core-0.2.x`): foto = sola striscia multifibra →
  auto-detect striscia + bande **in ordine norma** (seam-snapping), RGB→Lab→ΔE
  CIEDE2000 → grado grey-scale via **profili configurabili per famiglia norma**
  (ISO_105/AATCC/ASTM — soglie builtin = ESEMPIO, flaggate nel risultato),
  **scala grigia in-frame** (rilevamento riferimento neutro + white-balance,
  logica ISO 105-A11), colour-change vs Lab variante, **ripetibilità** su
  repliche (scarto max gradi), **strict mode** (rifiuto hard cattura scarsa),
  quality gate (blur/esposizione/fill) + confidence per banda.
- **Tarature/strumenti** (ISO 17025): registro `calibration_references`
  (scala grigia/piastrina/target/lightbox + certificato + scadenza) —
  **analisi BLOCCATA se riferimento scaduto/dismesso**; provenienza strumenti
  nel risultato.
- **Norme**: upload per-tenant della PROPRIA copia licenziata della norma
  (PDF) per metodo — non ridistribuiamo testo ISO (copyright-safe).
- **Report**: Digital Quality Report PDF + **SHA-256 sigillo di integrità**
  (NON firma qualificata) + ledger + verify + QR + **lock/finalize**
  (immutabile, ri-emissione bloccata 409) + **provenienza piena** nel PDF
  (sorgente, correzione colore, profilo grading, riferimenti+validità,
  ripetibilità, warning).
- **Validazione metodo**: campagne campioni software-vs-riferimento
  (spettrofotometro/visivo/lab esterno) con statistiche (scarto medio,
  % entro ±0.5 grado, bias, RMSE, pass indicativo ≥90%). Pronto a ricevere
  campioni reali. **È il documento di credibilità per l'accreditamento.**
- **Frontend** (mobile-first): Dashboard, Brand, Articoli, Batch, Prove
  (fibre auto da norma, fotocamera/webcam + upload, vision staining +
  colour-change, riferimenti strumenti, toggle in-frame grey-scale e strict),
  Norme (catalogo + upload norma), Report ledger (verifica/finalizza/PDF),
  Device (+ registro tarature). Silent token refresh.
- **Validazione & accreditamento (dentro il software, auto-aggiornante)**:
  modulo `/validation` (campagne software-vs-riferimento + statistiche) +
  **report PDF di validazione** (`GET /validation-runs/{id}/report`) +
  **prove interlaboratorio/PT** `/proficiency-tests` (registra round, calcola
  **z-score** = (x−X)/σ e **En** number, esito soddisfacente/discutibile/non
  soddisfacente — requisito ISO 17025 7.7.2; il circuito è del provider esterno) +
  **checklist accreditabilità** `GET /accreditation/readiness` (13 item calcolati
  live: campagne+%entro±0.5, riferimenti validi, norme caricate, report bloccati,
  PT soddisfacente, + item off-software incertezza/grading-validato/operatori/
  consulente/scopo Accredia) con livello maturità.
- **Verifica pubblica report**: QR del PDF → pagina pubblica `/verify/:id?h=<sha>`
  (no login) valido/non-valido; mirror RLS `report_verifications` (public read).
- **Correzione colore certificata**: piastrina/target con Lab certificato →
  white-balance ancorato al certificato (`in_frame_certified_white`).
- **Catalogo norme**: UNI EN ISO 105 (E/C/D/B/N/P/X) + AATCC (15/107/162/16/132/
  133/188/EP1/EP2, con equivalente ISO) + ASTM (D2244/E313) + **cuoio**
  (ISO 11640/11641/11642/15700/17700 + IULTCS IUF 421/426/434). Menu raggruppato
  per ente: UNI EN ISO 105 / AATCC / ASTM / Cuoio (ISO/IULTCS) / Interni.
- **Billing Stripe**: checkout (`POST /billing/checkout`) + webhook firmato
  (`/billing/webhook` → upsert subscription + `account_tier` per gating) +
  pagina Abbonamento (piani Trace/Vision Pro). Inattivo finché STRIPE_* non
  configurate (errore pulito). `[billing]` extra (stripe, lazy).
- **GDPR**: export/delete endpoint + template legali in `docs/legal/`.
- **Deploy**: `infra/Dockerfile.prod` (vision+storage), `render.yaml`,
  `infra/neon/setup_neon.sh`, storage **S3/R2** (`storage.py`, attivo con env).
- **Migrazioni Alembic**: 0001→0015 (testa: `0015_proficiency_tests`).

### Migrazioni chiave
`0001` schema completo+RLS · `0004` profili striscia · `0006` articoli+grading ·
`0007` ISO 105 + method_documents · `0008` calibration references + blocco
scadenze · `0009` report lock · `0010` validation samples · `0011` reference_values
(Lab certificato) · `0012` AATCC/ASTM · `0013` report_verifications (verifica
pubblica) · `0014` metodi cuoio · `0015` proficiency_tests (PT interlaboratorio).

## Setup locale

```bash
# Postgres 16 con ruolo solidita_app (vedi infra/postgres/init.sql)
cd backend && pip install -e ".[vision]"
python -m alembic upgrade head
uvicorn app.main:app --port 8000
cd ../frontend && npm i && npm run dev   # VITE_API_BASE=http://localhost:8000
pytest backend  # 69 verdi (serve Postgres)
```

Deploy: vedi **DEPLOY.md** (frontend su Vercel root=`frontend`; backend su
Railway/Render/Fly/VPS — NON su Vercel; DB consigliato: Neon/managed Postgres
con ruolo non-superuser).

## Cosa resta (in ordine)

1. **Deploy live** (codice 100% pronto): creare progetto **Neon** → lanciare
   `infra/neon/setup_neon.sh` (crea ruolo `solidita_app` + migra + verifica RLS);
   bucket **S3/R2** per le foto; backend su **Render** (`render.yaml`); frontend
   su **Vercel** (root=`frontend`). Vedi `DEPLOY.md`.
2. **Billing**: codice pronto — resta configurare account Stripe + price IDs
   (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_TRACE/VISION`) +
   email transazionali + observability/backup.
3. **App iOS nativa** — fatto: login+sessione, **selezione prova→config reale**,
   cattura nativa (lock esposizione/fuoco), **coda offline** (expo-file-system),
   privacy manifest + `STORE_LISTING.md`. Resta: frame-processor blur/esposizione
   (worklet; oggi tilt reale, blur/exposure stub), marker ArUco, **icona+screenshot**,
   Apple Developer + build (npm i → expo prebuild → Xcode/device) → TestFlight →
   submit. Niente IAP (abbonamenti sul web).
4. Hardening vision: marker ArUco + **omografia** (OpenCV), worker async per
   vision/PDF/email.

### Non-codice (bloccanti accreditamento — responsabilità business)
- Campioni reali 30→50→100 + confronto spettrofotometro/lab.
- Kit hardware certificato (dima, lightbox D65/TL84, scala grigia ISO,
  piastrina bianca, ColorChecker) con certificati.
- Consulente ISO/IEC 17025 + laboratorio conforme (si accredita il
  laboratorio+metodo, non l'app da sola).
- Licenze tabelle/soglie grading ufficiali (sostituire profili ESEMPIO).

## Mobile — decisione

- Il **portale web** resta la piattaforma di gestione (desktop + iPhone Safari).
- La **cattura accreditabile su iPhone 16 Pro richiede app iOS nativa**
  (AVFoundation): blocco esposizione/WB/fuoco, formati RAW, controllo torcia,
  telemetria sensori — Safari/getUserMedia NON espone questi controlli.
  La web app cattura "best effort" (ok per demo/pre-valutazione), la nativa è
  il passo per metrologia ripetibile. `mobile/` è lo skeleton predisposto.

## Regole non negoziabili (immutate)

1. RLS multi-tenant ovunque, ruolo DB non-superuser.
2. Nessuna formula/tabella ISO/AATCC proprietaria hardcoded: mapping configurabile.
3. SHA-256 = sigillo di integrità, mai "firma digitale qualificata".
4. Geometria e correzione colore SEPARATE nel pipeline.
5. iPhone = quality gate di cattura, non metrologia da solo: serve kit.
6. Fallback espliciti: ogni default non validato (soglie ESEMPIO, nessuna
   correzione colore, ordine fibre fallback) è flaggato nel risultato e nel PDF.

## Pipeline tecnica (implementata)

```
foto striscia → quality gate (blur/exposure/fill) [strict: rifiuto]
→ grey-scale in-frame → white balance neutro
→ auto-detect striscia → bande in ordine norma (seam snapping)
→ RGB → Lab → ΔE CIEDE2000 vs riferimento (batch zero | variante)
→ grado grey-scale (profilo per famiglia norma, ESEMPIO flaggato)
→ ripetibilità su repliche → brand rules pass/fail
→ report PDF + provenienza + SHA-256 → finalize/lock
```

## Commercial handoff (immutato nei principi)

Vendere: digitalizzazione laboratorio, report con sigillo hash, riduzione
soggettività, storico qualità, brand rules, tracciabilità strumenti.
NON vendere: certificazione ISO automatica, sostituzione laboratorio,
AI predittiva senza dataset.

Pricing indicativo: Trace setup 3.9-5.9k€ + 149-299€/m · Vision Pro setup
9.9-14.9k€ + 399-799€/m · Enterprise 24.9k€+ + 1.2-3k€/m.

## Letture per chi subentra

1. `README.md` · 2. `CLAUDE.md` (regole) · 3. `DEPLOY.md` · 4. questo file ·
5. `backend/app/db/migrations/versions/` (lo schema racconta il dominio) ·
6. memoria di build: `~/.claude/projects/...solidita.../memory/solidita-build-state.md`
