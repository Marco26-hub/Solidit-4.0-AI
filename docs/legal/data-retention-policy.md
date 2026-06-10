# Politica di Conservazione dei Dati — Solidità 4.0

> TEMPLATE — validare con legale. Configurabile per cliente nel contratto.

| Categoria | Conservazione predefinita | Note |
|-----------|---------------------------|------|
| Immagini raw acquisizione | 12 / 24 / 36 mesi (configurabile) | Cancellazione automatica a scadenza |
| Immagini corrette / ROI / thumbnail | come immagini raw | |
| Report PDF (quality_reports) | 5 / 10 anni | Valore probatorio/tracciabilità |
| Audit log | 5 / 10 anni | Append-only, immutabile |
| Dati utente/operatore | Durata contratto + `[N]` mesi | Poi cancellati/anonimizzati |
| Refresh token | Fino a scadenza/revoca | Rotazione + revoca |
| Backup | `[X]` giorni rolling | Cifrati, restore testato |

## Cancellazione
- **Su richiesta** (art. 17 GDPR): disattivazione immediata account + revoca sessioni
  (`POST /api/v1/account/delete`); cancellazione definitiva entro `[N]` giorni salvo
  obblighi di conservazione legali (es. fiscali sui report).
- **A fine contratto**: cancellazione o restituzione dati a scelta del Titolare (DPA §4).

## Eccezioni
Conservazione prolungata se richiesta da obblighi legali, contenziosi o sicurezza.
