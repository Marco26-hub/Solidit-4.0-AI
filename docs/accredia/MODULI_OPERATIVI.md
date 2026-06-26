# Moduli operativi — Solidità 4.0

> Template interni da copiare, compilare, firmare e archiviare nel sistema di
> gestione del laboratorio. I campi compilati devono riflettere dati reali.

Versione PDF compilabile:

- `../../output/pdf/accredia/Solidita_Accredia_Moduli_Compilabili.pdf`
- moduli singoli in `../../output/pdf/accredia/`

Rigenerazione:

```bash
python3 scripts/generate_accredia_fillable_pdfs.py
```

## MOD-01 — Piano validazione metodo

| Campo | Valore |
|---|---|
| Codice piano |  |
| Metodo/prova |  |
| Versione software |  |
| Versione algoritmo |  |
| Kit hardware / seriali |  |
| Profilo grading |  |
| Responsabile tecnico |  |
| Data approvazione |  |

### Disegno sperimentale

| Elemento | Descrizione |
|---|---|
| Numero campioni |  |
| Tipologie tessili |  |
| Fibre incluse |  |
| Range colori |  |
| Metodo riferimento |  |
| Numero repliche |  |
| Operatori coinvolti |  |
| Condizioni ambientali |  |

### Criteri di accettazione

| Metrica | Criterio |
|---|---|
| Accuratezza grado |  |
| Bias |  |
| RMSE |  |
| Ripetibilità |  |
| Riproducibilità |  |
| Robustezza |  |
| Tasso rigetto quality gate |  |

## MOD-02 — Rapporto validazione metodo

| Campo | Valore |
|---|---|
| Codice rapporto |  |
| Piano collegato |  |
| Dataset |  |
| Data inizio/fine |  |
| Versione software |  |
| Esito finale | Conforme / non conforme / conforme con limitazioni |

### Risultati

| Metrica | Risultato | Criterio | Esito |
|---|---:|---:|---|
| Campioni validi |  |  |  |
| % entro ±0,5 grado |  |  |  |
| Bias medio |  |  |  |
| RMSE |  |  |  |
| Scarto massimo repliche |  |  |  |
| Robustezza |  |  |  |

### Conclusione tecnica

- Limiti del metodo:
- Condizioni obbligatorie di uso:
- Casi esclusi:
- Azioni correttive richieste:
- Approvazione responsabile tecnico:

## MOD-03 — Budget incertezza

| Campo | Valore |
|---|---|
| Metodo/prova |  |
| Grandezza/risultato |  |
| Unità |  |
| Regola decisionale |  |
| Livello confidenza |  |

| Contributo | Tipo | Distribuzione | Valore | Divisore | Coefficiente sensibilità | Incertezza standard |
|---|---|---|---:|---:|---:|---:|
| Ripetibilità | A | normale |  |  |  |  |
| Riferimento colore | B |  |  |  |  |  |
| Lightbox / illuminazione | B |  |  |  |  |  |
| Geometria / ROI | B |  |  |  |  |  |
| Modello RGB→Lab | A/B |  |  |  |  |  |
| Profilo grading | B |  |  |  |  |  |

| Risultato | Valore |
|---|---:|
| Incertezza combinata `u_c` |  |
| Gradi di libertà effettivi |  |
| Fattore copertura `k` |  |
| Incertezza estesa `U` |  |
| Guard band |  |

## MOD-04 — Registro rischi e imparzialità

| ID | Rischio | Area | Probabilità | Impatto | Controllo | Responsabile | Stato |
|---|---|---|---|---|---|---|---|
| R-001 | Pressione commerciale su esito prova | Imparzialità |  |  | Doppia approvazione report |  | Aperto |
| R-002 | Uso senza kit hardware valido | Tecnico |  |  | Blocco software riferimenti |  | Aperto |
| R-003 | Profilo grading non validato | Metodo |  |  | Configurazione controllata |  | Aperto |
| R-004 | Accesso dati cross-tenant | Dati |  |  | RLS + test isolamento |  | Aperto |

## MOD-05 — Checklist audit interno

| Area | Domanda audit | Evidenza | Esito | Rilievo |
|---|---|---|---|---|
| Scopo | Lo scopo è chiaro e limitato? |  |  |  |
| SOP | Le SOP sono approvate e usate? |  |  |  |
| Strumenti | I riferimenti sono validi e tracciabili? |  |  |  |
| Metodo | La validazione copre l'uso dichiarato? |  |  |  |
| Incertezza | Il budget usa dati reali? |  |  |  |
| Report | I report dichiarano limiti e riferimenti? |  |  |  |
| Dati | RLS, audit e backup sono verificati? |  |  |  |
| Personale | Gli operatori sono autorizzati? |  |  |  |
| NC | Le non conformità sono gestite? |  |  |  |

## MOD-06 — Verbale riesame direzione

| Campo | Valore |
|---|---|
| Data |  |
| Partecipanti |  |
| Periodo riesaminato |  |
| Versione software riesaminata |  |
| Decisione su domanda Accredia | Procedere / rinviare / bloccare |

### Input obbligatori

- Esito audit interno:
- Stato azioni correttive:
- Stato validazione:
- Stato incertezza:
- Esiti PT/ILC:
- Reclami/non conformità:
- Risorse necessarie:
- Rischi residui:

### Decisioni

| Decisione | Responsabile | Scadenza |
|---|---|---|
|  |  |  |

## MOD-07 — Checklist freeze release accreditabile

| Controllo | Esito |
|---|---|
| Tag Git creato |  |
| Migrazioni database applicate |  |
| Test backend superati |  |
| Build frontend superata |  |
| Versione algoritmo registrata |  |
| Profili grading bloccati |  |
| Report di validazione collegato |  |
| Manuale e SOP revisionati |  |
