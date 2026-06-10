# HANDOFF.md — Solidità 4.0 Project Handoff

## Contesto

Solidità 4.0 è un progetto SaaS industriale per il controllo qualità tessile. Il prodotto nasce per aziende del distretto tessile, tintorie, stamperie e brand moda che vogliono digitalizzare prove, report, batch zero, controlli qualità e storico metrologico.

Il progetto non deve essere comunicato come sostituto immediato di un laboratorio accreditato. Deve essere comunicato come piattaforma di supporto, tracciabilità, pre-validazione e standardizzazione dei controlli qualità.

## Stato attuale

Siamo nella fase di progettazione production-ready.

Sono stati definiti:
- posizionamento commerciale;
- architettura tecnica;
- database multi-tenant;
- backend FastAPI;
- portale React;
- app iPhone;
- hardware kit;
- vision engine;
- report hash;
- roadmap sprint;
- principi compliance.

Non esiste ancora una codebase completa production-ready. Il prossimo step è avviare lo sviluppo guidato con Claude Code o team tecnico.

## Obiettivo prossimo

Costruire un MVP vendibile in due livelli:

### MVP 1 — Trace

SaaS per:
- aziende;
- utenti;
- reparti;
- brand specs;
- batch zero;
- test jobs;
- report PDF;
- hash SHA-256;
- certificate ledger;
- audit log.

### MVP 2 — Vision Base

Aggiunta di:
- app iPhone;
- acquisizione guidata;
- upload immagine;
- correzione geometrica;
- correzione colore configurabile;
- DeltaE CIEDE2000;
- grey scale mapping configurabile;
- pass/fail secondo brand rules.

## Decisioni già prese

### Hardware

Minimo commerciale consigliato:
- iPhone 16 Pro o superiore.

Compatibile:
- iPhone 15 Pro/Pro Max previa calibrazione.

Kit consigliato:
- lightbox D65/TL84;
- tile/reference standard;
- ColorChecker;
- dima fisica;
- app configurata;
- iPhone opzionale già configurato;
- MDM per clienti enterprise.

### Posizionamento

Frase corretta:
> Solidità 4.0 è il sistema operativo digitale del laboratorio qualità tessile.

Evitare:
> Certifica automaticamente secondo ISO.

### Report

Il report deve essere chiamato:
- Digital Quality Report;
- Report Digitale di Controllo Qualità Tessile.

Il codice SHA-256 deve essere definito:
- hash crittografico di integrità;
- sigillo tecnico di integrità.

Non chiamarlo firma digitale qualificata.

### Standard

Usare:
- ISO 105-A02/A03 come scale visive/reporting;
- ISO 105-A04/A05 per logiche strumentali;
- AATCC EP7/EP12 per valutazioni strumentali ove applicabile.

Non hardcodare formule protette da standard a pagamento. Creare mapping engine configurabile.

## Rischi principali

1. Vendere troppo presto come certificazione automatica.
2. Affidarsi solo all’iPhone senza dima/lightbox.
3. Confondere omografia con correzione colore.
4. Hardcodare formule ISO/AATCC senza licenza.
5. Non validare il sistema con campioni reali.
6. Mancanza di RLS/multi-tenant isolation.
7. Mancanza di audit trail.
8. Mancanza di contratti GDPR/DPA.
9. Promettere AI predittiva senza dataset.

## Regola tecnica fondamentale

La pipeline corretta è:

```
raw image
-> capture validation
-> marker detection
-> homography/geometric correction
-> color correction matrix/LUT
-> ROI segmentation
-> RGB to Lab
-> DeltaE CIEDE2000
-> configurable grey scale mapping
-> brand rules
-> pass/fail
-> signed/hash report
```

## Team handoff

Chi prende in mano il progetto deve prima leggere:

1. README.md
2. PRODUCT_SPEC.md
3. ARCHITECTURE.md
4. DATABASE_SCHEMA.md
5. CLAUDE.md
6. ROADMAP_SPRINT.md

Poi deve partire dallo Sprint 0 e Sprint 1, non dai moduli AI avanzati.

## Commercial handoff

Per il team commerciale:

Prodotto iniziale:
- Trace SaaS;
- Vision Pro Kit opzionale.

Non vendere:
- AI 60 FPS come già pronta;
- certificazione ISO automatica;
- sostituzione laboratorio.

Vendere:
- digitalizzazione laboratorio;
- report firmati con hash;
- riduzione soggettività;
- storico qualità;
- brand rules;
- velocità controllo;
- base dati per decisioni.

## Pricing handoff

Indicativo:

### Trace

Setup: 3.900 - 5.900 EUR  
Canone: 149 - 299 EUR/mese

### Vision Pro

Setup: 9.900 - 14.900 EUR  
Canone: 399 - 799 EUR/mese

### Vision Pro con iPhone configurato

Setup: 11.900 - 13.900+ EUR  
Canone: 499 - 799 EUR/mese

### Enterprise

Setup: 24.900 - 49.900+ EUR  
Canone: 1.200 - 3.000+ EUR/mese

## Prossima azione concreta

Creare repository monorepo:

```
solidita-4-0/
  backend/
  frontend/
  mobile/
  infra/
  docs/
```

Poi implementare:
1. auth;
2. companies;
3. RLS;
4. devices;
5. brand specs;
6. batch zero;
7. test jobs;
8. report ledger.

Solo dopo implementare Vision Engine.
