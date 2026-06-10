# Elenco Sub-Responsabili — Solidità 4.0

> TEMPLATE — aggiornare con i fornitori reali. Comunicare modifiche con `[N]` giorni di preavviso.

| Sub-responsabile | Servizio | Dati trattati | Sede / Regione | Garanzie |
|------------------|----------|---------------|----------------|----------|
| `[HOSTING/CLOUD]` | Hosting applicazione + DB | Tutti i dati piattaforma | UE `[REGIONE_HOSTING]` | DPA + ISO 27001 |
| `[OBJECT_STORAGE]` | Storage immagini/PDF (S3) | Immagini, report | UE | DPA + cifratura at-rest |
| `[EMAIL_PROVIDER]` | Email transazionali | Email, nome | UE/SCC | DPA |
| `[ERROR_MONITORING]` | Error tracking (opz.) | Log tecnici, IP | UE/SCC | DPA, scrubbing PII |
| `[BILLING]` (es. Stripe) | Pagamenti/abbonamenti | Dati fatturazione | UE/SCC | DPA, PCI-DSS |

Note:
- Trasferimenti extra-UE solo con Clausole Contrattuali Standard (SCC).
- Ogni sub-responsabile è vincolato da obblighi di protezione dati equivalenti (art. 28.4 GDPR).
