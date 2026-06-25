# Procedura domanda Accredia — Solidità 4.0

> Procedura interna di preparazione. Le domande ufficiali devono usare i moduli
> Accredia in vigore e devono essere riesaminate da un consulente qualificato e
> dal laboratorio richiedente.

## Obiettivo

Collegare prodotto, metodo, validazione, documentazione e attività del
laboratorio in una sequenza eseguibile per arrivare a una domanda coerente di
accreditamento o estensione dello scopo.

## Principio guida

Solidità 4.0 non viene presentato come laboratorio automatico. Viene presentato
come piattaforma digitale di controllo qualità tessile, tracciabilità,
pre-validazione e standardizzazione, usata da un laboratorio competente dentro
un sistema di gestione ISO/IEC 17025.

## Fase 0 — Decisione di perimetro

| Attività | Output | Responsabile |
|---|---|---|
| Definire prova/metodo e materiali coperti | Bozza scopo accreditamento | Direzione tecnica |
| Escludere usi non validati | Lista limiti dichiarati | Responsabile qualità |
| Identificare riferimenti normativi solo per codice | Elenco norme licenziate | Responsabile qualità |
| Definire se è nuova domanda o estensione | Strategia domanda | Direzione |

## Fase 1 — Freeze tecnico

| Attività | Output | Responsabile |
|---|---|---|
| Bloccare versione software | Tag Git/release, changelog | Responsabile software |
| Bloccare versione algoritmo | `algorithm_version` documentata | Responsabile tecnico |
| Bloccare kit hardware | Elenco seriali, codici, certificati | Laboratorio |
| Bloccare profili grading | Profilo validato/licenziato | Direzione tecnica |

Nessuna campagna di validazione deve essere usata per domanda formale se
algoritmo, hardware o profilo grading cambiano senza riesame.

## Fase 2 — Gap analysis

| Attività | Output |
|---|---|
| Compilare `MATRICE_REQUISITI_EVIDENZE.md` | Stato requisito per requisito |
| Compilare registro rischi | Rischi tecnici, imparzialità, cybersecurity |
| Verificare SOP | Elenco revisioni |
| Identificare evidenze esterne mancanti | Certificati, PT/ILC, tarature |

Decisione: procedere solo se i gap critici hanno un responsabile e una data.

## Fase 3 — Qualifica risorse e ambiente

| Attività | Output |
|---|---|
| Formare operatori | Registro formazione e prova pratica |
| Qualificare lightbox e ambiente | Report condizioni cattura |
| Verificare dima e riferimenti | Registro strumenti e certificati |
| Definire controlli pre-uso | Checklist operatore |

Il software deve rifiutare analisi quando i riferimenti obbligatori risultano
mancanti, scaduti o non compatibili con il metodo.

## Fase 4 — Validazione ingegneristica

| Attività | Output |
|---|---|
| Approvare piano validazione | Modulo piano firmato |
| Acquisire campioni reali rappresentativi | Dataset tracciato |
| Eseguire misure di riferimento | File sorgente o report laboratorio |
| Eseguire acquisizione Solidità 4.0 | Capture session e risultati |
| Calcolare metriche | Bias, RMSE, accuratezza, ripetibilità |
| Valutare robustezza | Scenari controllati |
| Approvare rapporto validazione | Rapporto firmato |

Il criterio minimo interno proposto è almeno 50 campioni e almeno 90% dei
risultati entro ±0,5 grado rispetto al riferimento, salvo criterio più severo
definito dal laboratorio o dal cliente.

## Fase 5 — Incertezza e regola decisionale

| Attività | Output |
|---|---|
| Identificare contributi Type A e Type B | Tabella contributi |
| Calcolare incertezza combinata | `u_c` |
| Calcolare incertezza estesa | `U`, fattore `k` |
| Definire guard band | Regola decisionale |
| Approvare budget | Budget incertezza firmato |

Il modulo `/colorimetry` supporta il calcolo, ma il budget è valido solo con
dati reali, riferimenti tarati e riesame metrologico.

## Fase 6 — Prove di validità continuativa

| Attività | Output |
|---|---|
| Pianificare controlli interni | Piano IQC |
| Eseguire repliche periodiche | Trend ripetibilità |
| Partecipare a PT/ILC o confronto equivalente | Esito e azioni |
| Gestire drift riferimenti | Azioni su scadenza/taratura |

## Fase 7 — Audit interno e riesame direzione

| Attività | Output |
|---|---|
| Eseguire audit interno completo | Rapporto audit |
| Aprire eventuali non conformità | Registro NC |
| Chiudere azioni correttive critiche | Verifica efficacia |
| Fare riesame direzione | Verbale e decisione domanda |

La domanda non deve partire con NC critiche aperte sul metodo, sulla riferibilità
o sull'integrità dei dati.

## Fase 8 — Preparazione domanda formale

| Attività | Output |
|---|---|
| Scaricare moduli Accredia aggiornati | Moduli ufficiali correnti |
| Compilare dati organizzazione | Domanda firmata |
| Compilare scopo richiesto | Allegato scopo |
| Allegare manuale/procedure/evidenze | Dossier |
| Allegare validazione e incertezza | Fascicolo tecnico |
| Riesame consulente | Verbale riesame |
| Invio domanda | Protocollo invio |

I nomi e le revisioni dei moduli ufficiali devono essere verificati al momento
della domanda, perché possono cambiare.

## Fase 9 — Valutazione e gestione rilievi

| Evento | Azione |
|---|---|
| Richiesta integrazioni | Tracciare documento, responsabile, scadenza |
| Rilievo documentale | Aprire NC/azione correttiva |
| Valutazione in campo | Preparare demo controllata con campioni reali |
| Osservazione tecnica | Riesaminare metodo e rischio impatto report |
| Chiusura rilievi | Archiviare evidenze e versioni |

## Condizioni minime per dire “pronti alla domanda”

- Scopo scritto e limitato.
- Manuale qualità revisionato.
- SOP approvate.
- Matrice evidenze compilata.
- Kit hardware completo con certificati.
- Campagna validazione conclusa e approvata.
- Incertezza approvata.
- PT/ILC eseguito o giustificazione approvata.
- Audit interno completato.
- Riesame direzione completato.
- Versione software congelata e tracciata.

