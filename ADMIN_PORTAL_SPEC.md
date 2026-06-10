# ADMIN_PORTAL_SPEC.md — Solidità 4.0 Web Portal

## Stack

- React
- TypeScript
- Tailwind CSS
- TanStack Query
- React Hook Form
- Zod
- Vite o Next.js

## Aree portale

### 1. Super Admin SaaS

Per gestione piattaforma:
- aziende;
- piani;
- stato abbonamento;
- dispositivi;
- kit spediti;
- usage;
- errori;
- report generati;
- audit;
- API keys.

### 2. Company Admin

Per azienda cliente:
- utenti;
- reparti;
- dispositivi;
- brand specs;
- batch zero;
- test jobs;
- report;
- dashboard KPI.

### 3. Lab Manager

Funzioni operative:
- crea batch zero;
- valida risultati;
- firma/approva report;
- gestisce tolleranze brand;
- consulta ledger.

## Componenti principali

### Dashboard

KPI:
- prove totali;
- pass rate;
- fail rate;
- prove per brand;
- prove per reparto;
- trend criticità;
- dispositivi attivi;
- calibrazioni scadute.

### Brand Spec Manager

Form:
- brand name;
- metodo test;
- fibra;
- max DeltaE;
- min grey scale;
- severity;
- notes.

### Batch Zero Registry

Campi:
- codice batch;
- fornitore;
- data apertura;
- data scadenza;
- Lab values per fibra;
- foto reference;
- stato.

### Certificate Ledger

Tabella:
- report number;
- brand;
- articolo;
- lotto;
- test;
- risultato;
- operatore;
- data;
- hash;
- PDF.

Azioni:
- view;
- download PDF;
- verify hash;
- export CSV;
- filter.

### Device Manager

Campi:
- modello;
- hardware UUID;
- stato MDM;
- ultima calibrazione;
- illuminante attivo;
- revoca device.

## Pass/Fail badges

- Green: pass
- Red: fail
- Yellow: review/manual verification

## UI tone

- pulito;
- industriale;
- premium;
- leggibile in laboratorio;
- pochi fronzoli;
- mobile friendly.
