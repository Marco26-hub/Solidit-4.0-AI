# SECURITY_COMPLIANCE.md — Solidità 4.0

## Principi

Solidità 4.0 gestisce dati aziendali sensibili: prove qualità, brand, commesse, immagini, report e operatori.

Serve sicurezza by design.

## GDPR

Dati personali possibili:
- utenti/operatori;
- email;
- log attività;
- audit trail;
- device associati.

Documenti necessari:
- Privacy Policy;
- Data Processing Agreement;
- termini SaaS;
- retention policy;
- subprocessor list;
- procedura data breach.

## Cybersecurity

Checklist:
- JWT access/refresh;
- password hashing Argon2/bcrypt;
- MFA opzionale;
- RBAC;
- PostgreSQL RLS;
- signed URLs;
- encryption at rest;
- HTTPS;
- rate limiting;
- audit log append-only;
- backup giornaliero;
- restore test;
- secrets in vault;
- dependency scanning;
- SAST;
- container scanning;
- SBOM;
- logging centralizzato;
- monitoring errori;
- alerting.

## Report hash

SHA-256 serve per integrità del PDF.

Non chiamarlo firma digitale qualificata.

Nome corretto:
- hash crittografico;
- sigillo tecnico di integrità;
- report integrity token.

## Audit log

Ogni azione critica deve essere loggata:
- login;
- creazione test;
- upload immagine;
- generazione report;
- download report;
- modifica brand rules;
- modifica batch zero;
- revoca device;
- override pass/fail.

## Data retention

Configurabile per cliente:
- immagini raw: 12/24/36 mesi;
- report PDF: 5/10 anni;
- audit log: 5/10 anni;
- dati utente: secondo contratto/GDPR.

## Device security

Se iPhone gestito:
- MDM;
- blocco rimozione profilo;
- aggiornamenti controllati;
- app allowlist;
- remote wipe;
- revoca device da backend.

## AI Act / AI governance

Il sistema è supporto decisionale qualità. Non deve essere presentato come sostituto autonomo del responsabile qualità.

Per moduli AI:
- versione modello;
- dataset lineage;
- metriche;
- human-in-the-loop;
- log decisione;
- possibilità override;
- validazione interna.
