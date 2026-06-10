# Informativa sulla Privacy — Solidità 4.0

> TEMPLATE — validare con legale. Ultimo aggiornamento: `[DATA]`.

## 1. Titolare del trattamento
`[TITOLARE]`, P.IVA `[P.IVA]`, sede `[SEDE]`. Contatto privacy: `[EMAIL_PRIVACY]`.
DPO (ove nominato): `[DPO]`.

## 2. Dati trattati
- **Account/operatori**: nome, email, ruolo, log di accesso, ultimo login.
- **Dispositivi**: identificativi hardware, modello, stato MDM.
- **Dati aziendali/qualità**: brand, commesse, articoli, lotti, prove, risultati,
  immagini, report, audit trail.
- **Tecnici**: indirizzo IP, user-agent, request-id, timestamp.

> Le immagini e i dati di prova sono dati **aziendali del cliente**; il cliente è
> Titolare e Solidità 4.0 agisce come **Responsabile** (vedi [DPA](dpa.md)).

## 3. Finalità e basi giuridiche
| Finalità | Base giuridica (art. 6 GDPR) |
|----------|------------------------------|
| Erogazione del servizio | Esecuzione del contratto (1.b) |
| Sicurezza, audit, antifrode | Legittimo interesse (1.f) |
| Adempimenti fiscali/contabili | Obbligo legale (1.c) |
| Comunicazioni di servizio | Esecuzione del contratto (1.b) |

## 4. Conservazione
Secondo la [Data Retention Policy](data-retention-policy.md). In sintesi:
immagini raw 12/24/36 mesi (configurabile), report 5/10 anni, audit log 5/10 anni.

## 5. Destinatari e sub-responsabili
Fornitori infrastruttura/hosting elencati in [subprocessors.md](subprocessors.md).
Nessun trasferimento extra-UE senza adeguate garanzie (SCC) — hosting in `[REGIONE_HOSTING]`.

## 6. Diritti dell'interessato (art. 15-22)
Accesso, rettifica, cancellazione, limitazione, portabilità, opposizione. Export
dati self-service: `GET /api/v1/account/export`. Cancellazione: `POST /api/v1/account/delete`.
Reclamo all'Autorità Garante (Garante Privacy).

## 7. Sicurezza
Hashing password (Argon2), JWT con rotazione refresh token, RLS multi-tenant,
cifratura in transito (HTTPS) e a riposo, rate limiting, audit log append-only,
backup. Dettagli: `SECURITY_COMPLIANCE.md`.

## 8. Modifiche
Le modifiche sostanziali saranno comunicate via email/portale con `[N]` giorni di preavviso.
