# Fascicolo Tecnico — Solidità 4.0

> **DRAFT interno.** Documentazione originale del metodo digitale di valutazione
> assistita della solidità colore. NON contiene testo delle norme ISO/UNI/AATCC
> (protette da copyright): le norme sono citate solo per identificativo. **Da
> revisionare da un consulente ISO/IEC 17025 prima di qualsiasi richiesta Accredia.**

## Scopo

Raccogliere metodo, procedure, tarature, validazione e tracciabilità del sistema
di digital imaging Solidità 4.0, in ottica di inseribilità in un percorso
ISO/IEC 17025 (l'accreditamento riguarda il **laboratorio e le prove nello scopo**,
non l'app o l'iPhone da soli).

## Posizionamento del metodo

Sistema di **imaging digitale per la pre-valutazione / valutazione assistita**
della solidità colore. NON è uno spettrofotometro e NON sostituisce un
laboratorio accreditato. La fotocamera RGB **stima** differenze cromatiche; non
misura curve spettrali.

## Limiti dichiarati

- Cattura RGB, non spettrale. ΔE su Lab derivato da RGB corretto.
- Correzione colore: matrice device (se tarata) **oppure** riferimento neutro
  in-frame (scala grigia/piastrina) — altrimenti RGB grezzo (flaggato nel report).
- Soglie ΔE→grado: profili **configurabili**; i profili builtin sono ESEMPIO
  non validati (segnalati nel risultato e nel report). Vanno sostituiti con
  profili validati/licenziati.
- Risultati affidabili solo con kit hardware (dima, lightbox, scala grigia,
  piastrina/target) e cattura entro i gate di qualità.

## Indice del fascicolo

| # | Documento | Stato | File |
|---|---|---|---|
| 1 | Perimetro tecnico-normativo | questo file | — |
| 2 | SOP acquisizione immagine | DRAFT | `SOP_01_acquisizione.md` |
| 3 | SOP gestione strumenti e tarature | DRAFT | `SOP_02_tarature.md` |
| 4 | SOP analisi colore | DRAFT | `SOP_03_analisi_colore.md` |
| 5 | SOP generazione report | DRAFT | `SOP_04_report.md` |
| 6 | SOP gestione software e versioni | DRAFT | `SOP_05_software_versioni.md` |
| 7 | SOP validazione del metodo | DRAFT | `SOP_06_validazione.md` |
| 8 | SOP gestione non conformità | DRAFT | `SOP_07_non_conformita.md` |
| 9 | SOP formazione operatori | DRAFT | `SOP_08_formazione.md` |
| 10 | Registri (strumenti/tarature/operatori/versioni/NC) | TEMPLATE | `REGISTRI.md` |
| 11 | Piano e report di validazione | da popolare con campioni reali | modulo app `/validation` |
| 12 | Manuale qualita ISO 17025 | DRAFT | `../accredia/MANUALE_QUALITA_ISO17025.md` |
| 13 | Validazione metodo ingegneristica | DRAFT | `../accredia/VALIDAZIONE_METODO_INGEGNERISTICA.md` |
| 14 | Matrice requisiti-evidenze | TEMPLATE | `../accredia/MATRICE_REQUISITI_EVIDENZE.md` |
| 15 | Procedura domanda Accredia | TEMPLATE | `../accredia/PROCEDURA_DOMANDA_ACCREDIA.md` |
| 16 | Moduli operativi | TEMPLATE | `../accredia/MODULI_OPERATIVI.md` |
| 17 | Stima incertezza | modulo software pronto, da compilare con dati reali | `/colorimetry` |
| 18 | Valutazione rischi | template disponibile | `../accredia/MODULI_OPERATIVI.md` |
| 19 | Report tipo + audit trail dimostrativo | generato dall'app | modulo Report |

## Riferimenti normativi (solo identificativi)

- ISO 105-A11 — logica imaging digitale per gradi di solidità (riferimento metodo).
- ISO 105-A02 (cambiamento colore), A03 (staining) — scale grigie.
- ISO 105-A05 — confronto strumentale.
- ISO/IEC 17025 — competenza laboratori di prova e taratura.

## Cosa è già implementato nel software (a supporto del fascicolo)

- Tracciabilità: audit trail append-only, `algorithm_version` su ogni risultato.
- Tarature: registro strumenti/riferimenti con **scadenza + blocco analisi** se
  scaduto/dismesso.
- Report: sigillo SHA-256, **lock/finalize** (immutabile), provenienza piena
  (sorgente, correzione colore, profilo grading, riferimenti, ripetibilità, warning).
- Validazione: modulo campagne software-vs-riferimento con statistiche
  (scarto medio, % entro ±0.5 grado, bias, RMSE).
- Ripetibilità: aggregazione repliche con scarto massimo gradi.
- Quality gate cattura + modalità strict (rifiuto cattura non idonea).
- Kit hardware obbligatorio per analisi colore/staining: lightbox + riferimenti
  fisici validi; il software blocca analisi se mancano riferimenti richiesti.
- Motore incertezza: contributi Type A/B, distribuzioni, Welch-Satterthwaite e
  guard band decisionale.
- Readiness accreditamento: checklist live su documenti, riferimenti,
  validazione, report bloccati e PT/ILC.

## Checklist maturità (sintesi — vedi SOP per dettaglio)

- [x] Metodo definito e documentato (questo fascicolo + SOP).
- [x] Software versionato e tracciabile.
- [x] Audit trail funzionante.
- [x] Report non modificabile dopo emissione.
- [x] Gestione strumenti/tarature con scadenze.
- [x] Modulo validazione pronto.
- [ ] Validazione con 50–100 campioni reali vs spettrofotometro/lab.
- [x] Modulo calcolo incertezza GUM/guard band pronto.
- [x] Manuale qualita ISO/IEC 17025 draft.
- [x] Matrice requisiti-evidenze draft.
- [x] Procedura domanda Accredia draft.
- [x] Moduli operativi draft.
- [ ] Budget incertezza compilato con dati reali.
- [ ] Profili grading validati/licenziati (sostituire ESEMPIO).
- [ ] SOP riviste da consulente qualificato.
- [ ] Kit hardware con certificati.
- [ ] Laboratorio conforme ISO/IEC 17025.

**Livello attuale: metodo pre-validato / strumento interno.** Per "pronto per
laboratorio" mancano le voci non spuntate (in larga parte non-codice).
