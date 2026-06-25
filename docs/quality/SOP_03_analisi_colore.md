# SOP-03 — Analisi colore

> DRAFT interno. Da rivedere con consulente ISO/IEC 17025.

**Scopo.** Definire la pipeline di calcolo dal file immagine al grado di solidità.

**Responsabilità.** Tecnico laboratorio (esecuzione/verifica), Responsabile
qualità (riesame profili grading).

## Pipeline (implementata)

1. Verifica kit hardware/tarature: l'analisi è bloccata se mancano i riferimenti
   minimi validi o se sono scaduti/dismessi.
2. Quality gate cattura (blur/esposizione/fill); strict → rifiuto.
3. Correzione colore: matrice device **oppure** white-balance da riferimento
   neutro in-frame; se assente → RGB grezzo (flag `colour_correction: none`).
4. Localizzazione automatica striscia + segmentazione bande **in ordine norma**
   (snap ai seam di colore).
5. RGB → CIELAB → ΔE CIEDE2000 vs riferimento (batch zero per staining; Lab
   variante per colour-change).
6. Mapping ΔE → grado grey-scale tramite **profilo configurabile** per famiglia
   norma (ISO_105 / AATCC / ASTM).
7. Ripetibilità: se presenti più repliche, ΔE medio + scarto massimo gradi.
8. Pass/fail vs regole capitolato brand (se associato).

## Controlli e segnalazioni (provenienza)

- Profilo grading usato; se ESEMPIO non validato → warning.
- Ordine fibre: `strip_profile` (garantito) o fallback (warning).
- Confidence per banda; correzione colore applicata; warning qualità.

## Regola

I profili grading **builtin sono ESEMPIO**: prima dell'uso accreditato vanno
sostituiti con profili validati/licenziati (vedi SOP-06).

## Riferimenti

ISO 105-A02/A03 (scale), A05 (strumentale), SOP-06 (validazione).
