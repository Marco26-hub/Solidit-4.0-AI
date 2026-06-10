# ROADMAP_SPRINT.md — Solidità 4.0

## Obiettivo

Sviluppare il prodotto in sprint ordinati, evitando di costruire subito tutto.

## Sprint 0 — Repository & Setup

Output:
- monorepo;
- backend;
- frontend;
- mobile;
- docker-compose;
- .env.example;
- CLAUDE.md;
- CI base.

Done quando:
- app avviabili localmente;
- database migrabile;
- test base verdi.

## Sprint 1 — Backend Core

Output:
- FastAPI;
- auth;
- users;
- companies;
- memberships;
- departments;
- devices;
- RLS;
- Alembic migrations.

Done quando:
- login funziona;
- tenant isolation testata;
- CRUD base operativo.

## Sprint 2 — Quality Domain

Output:
- brand specs;
- acceptance rules;
- multifiber batches;
- test methods;
- test jobs;
- capture sessions.

Done quando:
- Lab Manager può creare brand rules e batch zero;
- operatore può creare test job.

## Sprint 3 — Vision Engine Base

Output:
- image upload;
- capture validation;
- homography;
- color correction placeholder/configurable;
- Lab conversion;
- DeltaE;
- grade mapping configurable;
- result persistence.

Done quando:
- sample image produce risultato JSON.

## Sprint 4 — Report Service

Output:
- PDF generation;
- SHA-256 hash;
- QR verify;
- report ledger;
- download signed URL.

Done quando:
- report generato, scaricabile e verificabile.

## Sprint 5 — Admin Portal

Output:
- dashboard;
- brand spec manager;
- batch zero registry;
- certificate ledger;
- device manager.

Done quando:
- flusso completo web è usabile.

## Sprint 6 — Mobile MVP

Output:
- login;
- barcode;
- workflow selection;
- guided capture UI;
- telemetry mock/native first pass;
- upload;
- result view.

Done quando:
- tecnico può fare una prova da mobile.

## Sprint 7 — Hardware Kit Pilot

Output:
- dima prototipo;
- lightbox selezionata;
- reference card/tile;
- procedura calibrazione;
- manuale operativo.

Done quando:
- 10 acquisizioni ripetute danno risultati stabili.

## Sprint 8 — Validation Pilot

Output:
- test con 30-50 campioni;
- confronto laboratorio/spettrofotometro;
- report accuratezza;
- correzione pipeline.

Done quando:
- accuratezza e ripetibilità documentate.

## Sprint 9 — Commercial Pilot

Output:
- 3 aziende pilota;
- contratti;
- onboarding;
- supporto;
- feedback;
- pricing finale.

Done quando:
- prima azienda usa il sistema in ambiente reale.

## Sprint 10 — Production Hardening

Output:
- monitoring;
- backup;
- security hardening;
- audit;
- documentation;
- SLA;
- runbook.

Done quando:
- piattaforma pronta per clienti paganti.
