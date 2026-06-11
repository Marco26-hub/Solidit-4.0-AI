# SOP-05 — Gestione software e versioni

> DRAFT interno. Da rivedere con consulente ISO/IEC 17025.

**Scopo.** Garantire tracciabilità e controllo delle versioni di software e
algoritmo di analisi.

**Responsabilità.** Responsabile tecnico (rilascio), Responsabile qualità
(approvazione cambi che impattano la prova).

## Regole

- Ogni risultato registra `algorithm_version` (es. `vision-core-0.2.x`).
- Cambi all'algoritmo che possono alterare ΔE/grado richiedono:
  1. nota di rilascio (changelog);
  2. ri-verifica su set di controllo (sotto-insieme della campagna di validazione);
  3. approvazione qualità prima della messa in produzione.
- Versioni app iOS / backend tracciate (tag git, registro versioni).
- Aggiornamenti iOS/dipendenze che toccano la pipeline camera → ri-verifica
  cattura prima dell'uso operativo.

## Registrazioni

Registro versioni software (vedi `REGISTRI.md`); tag/commit nel repository.

## Riferimenti

SOP-06 (validazione/ri-verifica).
