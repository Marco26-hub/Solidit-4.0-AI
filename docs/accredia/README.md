# Dossier Accredia - Solidita 4.0

> Draft operativo interno. Da riesaminare e approvare da un laboratorio e da un
> consulente ISO/IEC 17025 prima di qualsiasi domanda formale ad Accredia.

## Scopo

Questa cartella raccoglie i documenti necessari per portare Solidita 4.0 da
piattaforma di pre-validazione a strumento/software validato dentro un sistema di
gestione laboratorio ISO/IEC 17025.

L'accreditamento non riguarda l'app da sola: riguarda il laboratorio, il metodo,
le persone, gli strumenti, l'ambiente, la riferibilita, l'incertezza e lo scopo
di accreditamento dichiarato.

## Documenti

| Documento | Uso |
|---|---|
| `MANUALE_QUALITA_ISO17025.md` | Manuale qualita laboratorio, con controlli organizzativi e tecnici |
| `VALIDAZIONE_METODO_INGEGNERISTICA.md` | Protocollo tecnico per validare il metodo digitale RGB->Lab->DeltaE->grado |
| `MATRICE_REQUISITI_EVIDENZE.md` | Collegamento tra requisiti, SOP, software, evidenze e gap residui |
| `PROCEDURA_DOMANDA_ACCREDIA.md` | Sequenza operativa per preparare domanda o estensione dello scopo |
| `MODULI_OPERATIVI.md` | Template compilabili per validazione, incertezza, audit, rischi e riesame |

## PDF compilabili

I moduli operativi sono disponibili anche come PDF A4 con campi AcroForm
scrivibili:

- `../../output/pdf/accredia/Solidita_Accredia_Moduli_Compilabili.pdf`
- `../../output/pdf/accredia/MOD-01_piano_validazione_metodo_compilabile.pdf`
- `../../output/pdf/accredia/MOD-02_rapporto_validazione_metodo_compilabile.pdf`
- `../../output/pdf/accredia/MOD-03_budget_incertezza_compilabile.pdf`
- `../../output/pdf/accredia/MOD-04_registro_rischi_e_imparzialita_compilabile.pdf`
- `../../output/pdf/accredia/MOD-05_checklist_audit_interno_compilabile.pdf`
- `../../output/pdf/accredia/MOD-06_verbale_riesame_direzione_compilabile.pdf`
- `../../output/pdf/accredia/MOD-07_checklist_freeze_release_accreditabile_compilabile.pdf`

Rigenerazione:

```bash
python3 scripts/generate_accredia_fillable_pdfs.py
```

## Ordine di lavoro consigliato

1. Definire lo scopo tecnico limitato della prova.
2. Compilare la matrice requisiti-evidenze.
3. Revisionare manuale qualita, SOP e fascicolo tecnico.
4. Congelare versione software, algoritmo, hardware e profili grading.
5. Eseguire validazione ingegneristica con campioni reali.
6. Compilare budget incertezza e regola decisionale.
7. Eseguire audit interno e riesame direzione.
8. Scaricare e compilare i moduli Accredia ufficiali aggiornati.

## Collegamento software-documentazione

| Area | Documento guida | Modulo software |
|---|---|---|
| Readiness accreditamento | `MATRICE_REQUISITI_EVIDENZE.md` | `/api/v1/accreditation/readiness` |
| Tarature e riferimenti | `SOP_02_tarature.md` | Registro riferimenti fisici |
| Acquisizione vincolata al kit | `SOP_01_acquisizione.md` | Vision analysis con reference check |
| Analisi colore | `SOP_03_analisi_colore.md` | Pipeline geometry + color correction |
| Validazione metodo | `VALIDAZIONE_METODO_INGEGNERISTICA.md` | `/validation` |
| Incertezza | `MODULI_OPERATIVI.md` | `/colorimetry` |
| Report ufficiali | `SOP_04_report.md` | Report lock + SHA-256 integrity hash |

## Collegamenti ai documenti gia presenti

- `docs/quality/FASCICOLO_TECNICO.md`
- `docs/quality/SOP_01_acquisizione.md`
- `docs/quality/SOP_02_tarature.md`
- `docs/quality/SOP_03_analisi_colore.md`
- `docs/quality/SOP_04_report.md`
- `docs/quality/SOP_05_software_versioni.md`
- `docs/quality/SOP_06_validazione.md`
- `docs/quality/SOP_07_non_conformita.md`
- `docs/quality/SOP_08_formazione.md`
- `docs/quality/REGISTRI.md`

## Output da produrre prima della domanda

- Scopo di accreditamento proposto, limitato a prove/metodi specifici.
- Elenco apparecchiature e riferimenti fisici, con certificati.
- Piano validazione approvato.
- Dataset di validazione con campioni reali.
- Rapporto validazione compilato.
- Budget incertezza compilato con dati reali.
- Evidenze di repeatability, reproducibility e robustness.
- Evidenze PT/ILC o giustificazione documentata.
- Audit interno e riesame direzione.

## Cosa non e ancora automatico

- La compilazione dei moduli Accredia ufficiali.
- La certificazione dei riferimenti fisici.
- La qualifica degli operatori.
- La validazione con campioni reali.
- L'approvazione metrologica del budget incertezza.
- La decisione dell'ente di accreditamento.
