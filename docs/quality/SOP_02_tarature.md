# SOP-02 — Gestione strumenti e tarature

> DRAFT interno. Da rivedere con consulente ISO/IEC 17025.

**Scopo.** Garantire che dispositivi e riferimenti fisici siano identificati,
certificati e in validità; impedire prove con strumenti scaduti.

**Responsabilità.** Responsabile qualità (approvazione), Tecnico laboratorio
(registrazione/verifiche).

## Strumenti e riferimenti registrati

- Dispositivo iPhone: seriale, modello, versione iOS, profilo calibrazione
  (matrici D65/TL84 se presenti).
- Light box (codice, data verifica).
- Scala grigia ISO fisica (codice, n° certificato, scadenza).
- Piastrina bianca certificata, target colore (ColorChecker).

## Regole di validità (implementate nel software)

- Ogni riferimento ha `kind`, `code`, n° certificato, `valid_from`/`valid_until`,
  stato (attivo/dismesso).
- Stato calcolato: **valido / in scadenza (≤30 gg) / scaduto / dismesso**.
- **L'analisi è BLOCCATA** se un riferimento collegato alla cattura è scaduto o
  dismesso (errore `reference_invalid`).
- Analisi Vision senza kit minimo collegato → **BLOCCATA**. Per staining sono
  richiesti light box, scala grigia e piastrina bianca validi; per colour-change
  sono richiesti light box e piastrina bianca validi.

## Procedura periodica

1. Verifica/ricalibrazione secondo periodicità definita (es. annuale per scala
   grigia/target; verifica light box).
2. Aggiornare `valid_until` + allegare certificato.
3. Dismettere i riferimenti non più conformi (stato "dismesso").
4. Riesame scadenze (alert "in scadenza" nel gestionale Device → Riferimenti).

## Registrazioni

Registro strumenti + registro tarature/verifiche (vedi `REGISTRI.md`); log audit
delle creazioni/dismissioni.

## Riferimenti

ISO/IEC 17025 (riferibilità), SOP-01, SOP-03.
