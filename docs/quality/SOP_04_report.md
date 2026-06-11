# SOP-04 — Generazione e gestione report

> DRAFT interno. Da rivedere con consulente ISO/IEC 17025.

**Scopo.** Definire emissione, integrità e immutabilità del Digital Quality Report.

**Responsabilità.** Tecnico/Responsabile qualità (generazione/finalizzazione).

## Contenuto report (implementato)

Dati prova (azienda, articolo/lotto, metodo, operatore, data), risultati (Lab,
ΔE, grado per fibra, pass/fail), **provenienza** (sorgente, correzione colore,
profilo grading con flag ESEMPIO, riferimenti+validità, ripetibilità, warning),
disclaimer, **SHA-256 sigillo di integrità**, QR di verifica.

## Regole

- Il report è uno snapshot immutabile (payload congelato + hash).
- **Finalize/lock**: una volta bloccato è l'emissione ufficiale; non è possibile
  emettere un altro report sulla stessa prova (errore `report_locked`, HTTP 409).
- SHA-256 = **sigillo tecnico di integrità**, NON firma digitale qualificata.
- Disclaimer obbligatorio: imaging digitale, non misura spettrale, non sostituto
  di laboratorio accreditato.
- Verifica integrità: endpoint `/reports/{id}/verify` ricalcola l'hash.

## Audit

Audit trail append-only su creazione/finalizzazione (chi/quando). UPDATE/DELETE
revocati a livello DB sull'audit log.

## Riferimenti

SOP-03 (analisi), SOP-05 (versioni software).
