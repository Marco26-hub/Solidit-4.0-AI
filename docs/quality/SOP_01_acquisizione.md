# SOP-01 — Acquisizione immagine

> DRAFT interno. Da rivedere con consulente ISO/IEC 17025.

**Scopo.** Definire come acquisire l'immagine della striscia multifibra (e del
tessuto per il colour-change) in modo ripetibile e tracciabile.

**Campo di applicazione.** Tutte le prove di solidità colore valutate con
Solidità 4.0.

**Responsabilità.** Operatore (esecuzione), Tecnico laboratorio (verifica setup),
Responsabile qualità (riesame).

## Prerequisiti (bloccanti)

1. Dispositivo iPhone identificato (seriale registrato in app, vedi SOP-02).
2. Light box in stato "valido" (vedi registro tarature).
3. Scala grigia ISO fisica + piastrina bianca/target validi (non scaduti).
4. Dima fisica per crop canonico della striscia.
5. Sfondo neutro, nessun riflesso/ombra/piega.

## Procedura

1. Registrare la prova: articolo/variante, lotto multifibra (batch zero),
   metodo (solidità), riferimenti strumenti usati (light box, scala grigia).
2. Posizionare la striscia nella dima; la **prima fibra della norma a sinistra**
   (l'app mappa le bande in ordine secondo il profilo striscia del lotto).
3. Se previsto, includere la **scala grigia in-frame** e attivare il flag
   relativo (correzione colore in-frame, logica ISO 105-A11).
4. Per cattura accreditabile usare l'**app iOS nativa** (esposizione/fuoco/WB
   bloccati). La cattura web è ammessa solo per pre-valutazione.
5. Attivare la **modalità accreditamento (strict)**: la cattura viene rifiutata
   se non supera i gate.

## Gate di qualità (cattura rifiutata se)

- Sfocatura (blur) sotto soglia.
- Sotto/sovraesposizione o zone bruciate oltre soglia.
- Striscia che occupa poco del fotogramma (fill basso).
- Scala grigia richiesta ma non rilevata.
- (Nativa) tilt/movimento oltre tolleranza.

## Registrazioni

- Sessione di cattura + immagini (storage con hash SHA-256).
- Riferimenti strumenti collegati (provenienza nel risultato).
- Telemetria cattura (tilt, blur/exposure flags).

## Riferimenti

ISO 105-A11 (logica imaging), SOP-02 (strumenti), SOP-03 (analisi).
