# Procedura Violazione Dati (Data Breach) — art. 33-34 GDPR

> TEMPLATE — validare con legale. Owner: `[RESPONSABILE_SICUREZZA]`.

## 1. Rilevamento
Fonti: alerting/monitoring, error tracking, audit log, segnalazioni. Chiunque rilevi
un sospetto deve notificare immediatamente `[EMAIL_SICUREZZA]`.

## 2. Classificazione e contenimento (entro 24h)
- Valutare natura, categorie e volume dei dati, gravità e rischio per gli interessati.
- Contenere: revoca sessioni/token, rotazione segreti, isolamento sistemi, blocco device.

## 3. Notifica
- **Al Garante**: entro **72 ore** dalla conoscenza, se vi è rischio per i diritti
  e le libertà degli interessati (art. 33).
- **Agli interessati**: senza ingiustificato ritardo se **rischio elevato** (art. 34).
- **Al Titolare cliente** (quando Solidità è Responsabile): senza ingiustificato
  ritardo (DPA §4).

## 4. Registro
Ogni violazione è documentata nel **registro dei data breach**: data, descrizione,
dati coinvolti, effetti, misure adottate.

## 5. Post-incident
Root cause analysis, misure correttive, aggiornamento controlli e runbook.

## Contenuto minimo della notifica
Natura della violazione · categorie e numero approssimativo di interessati/record ·
contatti (`[DPO]`/`[EMAIL_SICUREZZA]`) · conseguenze probabili · misure adottate/proposte.
