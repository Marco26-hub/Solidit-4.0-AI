# SOP-06 — Validazione del metodo

> DRAFT interno. Da rivedere con consulente ISO/IEC 17025.

**Scopo.** Definire come dimostrare che il metodo digitale concorda con un
metodo di riferimento (spettrofotometro / valutazione esperta / laboratorio).

**Responsabilità.** Responsabile qualità (piano e accettazione), Tecnico
(esecuzione).

## Fasi (campioni)

- Iniziale: ≥30 campioni.
- Pre-validazione: ≥50 campioni, più operatori, più giorni.
- Robusta: ≥100 campioni, campioni ciechi, confronto esterno.

## Copertura campioni

Colori chiari/scuri/saturi/pastello; tessuti lucidi/opachi; trame e materiali
diversi; vari livelli di cambiamento e di staining.

## Per ogni campione

Registrare nel modulo app `/validation`: grado software, grado riferimento
(spettrofotometro/visivo/lab), metodo di riferimento. Opzionale: ΔE software/rif.

## Statistiche calcolate (automatiche)

- n campioni valutati;
- scarto medio assoluto in gradi;
- **% risultati entro ±0.5 grado**;
- bias (sistematico);
- RMSE;
- scarto massimo.
- Ripetibilità (intra-operatore) e riproducibilità (inter-operatore): da campagne
  dedicate con repliche.

## Criteri di accettazione (indicativi — da confermare con consulente)

- ≥ 90–95% dei risultati entro ±0.5 grado.
- Bias contenuto e gestione esplicita dei risultati borderline.
- Ripetibilità accettabile; nessun pattern sistematico fuori tolleranza.

## Output

Report di validazione (esportabile dal modulo) + correzione profili grading se
necessario. È il **documento di credibilità** per il consulente/laboratorio.

Per il disegno sperimentale completo, includere anche
`docs/accredia/VALIDAZIONE_METODO_INGEGNERISTICA.md`: stratificazione campioni,
repeatability, reproducibility, MSA/Gage R&R, incertezza e guard band.

## Riferimenti

ISO 105-A05 (confronto strumentale), SOP-03, SOP-05.
