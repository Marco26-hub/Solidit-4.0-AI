# Matrice requisiti-evidenze — Solidità 4.0

> Documento operativo interno. Non sostituisce il testo ufficiale ISO/IEC 17025
> e non contiene estratti proprietari. La matrice collega requisiti, evidenze,
> procedure e funzioni software da usare nel percorso di accreditamento del
> laboratorio.

## Scopo

Fornire una vista unica di:

- requisiti tecnici e gestionali da presidiare;
- documenti Solidità 4.0 che li coprono;
- evidenze da raccogliere prima della domanda formale;
- moduli software coinvolti;
- gap residui non risolvibili solo con il codice.

L'accreditamento resta riferito al laboratorio, al metodo dichiarato nello scopo,
agli operatori, all'ambiente, agli strumenti e alla riferibilità metrologica.
Solidità 4.0 supporta tracciabilità, standardizzazione, pre-validazione e
controllo dati.

## Legenda stato

| Stato | Significato |
|---|---|
| Pronto software | Funzione implementata e utilizzabile nel prodotto |
| Template | Documento/modulo presente, da compilare con dati reali |
| Da validare | Richiede campagna sperimentale, riesame tecnico o consulente |
| Esterno | Richiede laboratorio, ente, fornitore o certificato fuori piattaforma |

## Matrice

| Area | Evidenza richiesta | Documenti / moduli | Software | Stato | Gap residuo |
|---|---|---|---|---|---|
| Imparzialità | Analisi rischi, responsabilità, gestione pressioni commerciali | `MANUALE_QUALITA_ISO17025.md`, `MODULI_OPERATIVI.md` | Audit trail | Template | Compilare registro rischi e approvazione direzione |
| Riservatezza | Regole accesso, protezione dati cliente, NDA dove applicabile | `MANUALE_QUALITA_ISO17025.md`, `SECURITY_COMPLIANCE.md` | Multi-tenant RLS, ruoli, audit | Pronto software | Riesame legale privacy/contratti |
| Struttura laboratorio | Organigramma, ruoli, responsabilità, sostituti | `MANUALE_QUALITA_ISO17025.md`, `MODULI_OPERATIVI.md` | Utenti e membership aziendale | Template | Nomine firmate dal laboratorio |
| Personale | Qualifica operatori, addestramento, autorizzazioni | `SOP_08_formazione.md`, `REGISTRI.md` | Registro audit e utenti | Template | Prove pratiche e firme operatori |
| Ambienti | Condizioni di cattura, lightbox, controllo illuminazione | `SOP_01_acquisizione.md`, `SOP_02_tarature.md` | Quality gate cattura | Da validare | Misure ambientali e criteri accettazione |
| Apparecchiature | Dima, lightbox, scala grigia, white tile, target colore | `SOP_02_tarature.md`, `REGISTRI.md` | Registro riferimenti e blocco scadenze | Pronto software | Certificati esterni e piano tarature |
| Riferibilità | Catena metrologica dei riferimenti fisici | `SOP_02_tarature.md` | `calibration_references` | Esterno | Certificati tracciabili e criteri di validità |
| Fornitori esterni | Valutazione fornitori, certificati, PT, tarature | `MANUALE_QUALITA_ISO17025.md`, `MODULI_OPERATIVI.md` | Allegati/documenti metodo | Template | Elenco fornitori approvati |
| Riesame richieste | Conferma metodo, scopo, limiti e accettazione cliente | `MANUALE_QUALITA_ISO17025.md` | Batch/test job/report | Template | Modulo richiesta prova firmato |
| Metodo | Metodo digitale RGB corretto → Lab → ΔE → grado | `FASCICOLO_TECNICO.md`, `SOP_03_analisi_colore.md` | Vision pipeline | Da validare | Approvazione tecnica e scopo limitato |
| Validazione metodo | Accuratezza, bias, ripetibilità, riproducibilità, robustezza | `VALIDAZIONE_METODO_INGEGNERISTICA.md`, `SOP_06_validazione.md` | `/validation` | Template | Dataset reale 50–100+ campioni |
| Incertezza | Budget GUM, contributi Type A/B, guard band | `MODULI_OPERATIVI.md`, `VALIDAZIONE_METODO_INGEGNERISTICA.md` | `/colorimetry` | Pronto software | Valori reali e approvazione metrologica |
| Campionamento | Identificazione campioni, criteri inclusione/esclusione | `SOP_06_validazione.md` | Dataset validation | Template | Piano campionamento firmato |
| Gestione oggetti prova | Codifica, stato, catena custodia, conservazione | `REGISTRI.md`, `MANUALE_QUALITA_ISO17025.md` | Batch, capture session, report | Da validare | Registro fisico/lab dei campioni |
| Registrazioni tecniche | Dati grezzi, versioni algoritmo, riferimenti usati, warning | `SOP_04_report.md`, `SOP_05_software_versioni.md` | Audit, report payload, hash | Pronto software | Policy retention e backup approvata |
| Validità risultati | Controlli interni, repliche, drift, carte controllo | `SOP_06_validazione.md`, `MODULI_OPERATIVI.md` | Repeatability, PT record | Da validare | Piano controlli periodici |
| PT / ILC | Partecipazione o confronto interlaboratorio equivalente | `MANUALE_QUALITA_ISO17025.md` | `proficiency_tests` | Esterno | Round PT/ILC soddisfacente o giustificazione |
| Reporting | Report chiaro, limiti, riferimenti, integrità, stato finale | `SOP_04_report.md` | Report lock + SHA-256 | Pronto software | Firma/approvazione laboratorio |
| Reclami | Ricezione, valutazione, azione, risposta | `MANUALE_QUALITA_ISO17025.md`, `MODULI_OPERATIVI.md` | Audit trail | Template | Registro reclami operativo |
| Non conformità | Blocco lavoro, analisi causa, correzioni, ripresa | `SOP_07_non_conformita.md` | Warning/quality gate/audit | Template | Registro NC e responsabilità |
| Dati e sistemi informativi | Accessi, backup, RLS, versioning, modifica controllata | `SECURITY_COMPLIANCE.md`, `SOP_05_software_versioni.md` | RLS, migration, audit | Pronto software | Piano backup/restore verificato |
| Documenti | Controllo revisioni, approvazioni, distribuzione | `MANUALE_QUALITA_ISO17025.md` | Git, release tag | Template | Registro approvazione documenti |
| Rischi e opportunità | Rischi tecnici, commerciali, metrologici, cybersecurity | `MODULI_OPERATIVI.md` | Readiness dashboard | Template | Registro rischi vivo |
| Miglioramento | Azioni migliorative, trend errori, revisioni metodo | `MANUALE_QUALITA_ISO17025.md` | Analytics validazione | Template | Riesami periodici |
| Azioni correttive | Causa radice, azione, efficacia | `SOP_07_non_conformita.md`, `MODULI_OPERATIVI.md` | Audit trail | Template | Evidenza efficacia |
| Audit interno | Piano, checklist, rilievi, follow-up | `MODULI_OPERATIVI.md` | Readiness + report | Template | Audit interno completato |
| Riesame direzione | Input, decisioni, risorse, obiettivi | `MODULI_OPERATIVI.md` | KPI readiness | Template | Verbale approvato |

## Evidenze minime per passare da software a pratica accreditabile

1. Scopo limitato e scritto, con metodo/prove esatte.
2. Kit hardware identificato, controllato, tarato e vincolante.
3. Campagna di validazione su campioni reali e rappresentativi.
4. Confronto con riferimento qualificato: spettrofotometro, valutatore esperto o laboratorio esterno.
5. Budget incertezza compilato con dati reali.
6. Profili grading configurabili validati o licenziati.
7. Report finali con limiti dichiarati e hash di integrità.
8. Audit interno, riesame direzione e azioni correttive chiuse.

