# PDF compilabili Accredia - Solidita 4.0

Questa cartella contiene template PDF interni con campi AcroForm scrivibili.

> Nota: sono moduli operativi Solidita 4.0 per preparare il dossier. Non
> sostituiscono i moduli ufficiali Accredia vigenti, da scaricare e compilare al
> momento della domanda formale.

## Bundle completo

- `Solidita_Accredia_Moduli_Compilabili.pdf` - tutti i moduli in un unico PDF.

## Moduli singoli

- `MOD-01_piano_validazione_metodo_compilabile.pdf`
- `MOD-02_rapporto_validazione_metodo_compilabile.pdf`
- `MOD-03_budget_incertezza_compilabile.pdf`
- `MOD-04_registro_rischi_e_imparzialita_compilabile.pdf`
- `MOD-05_checklist_audit_interno_compilabile.pdf`
- `MOD-06_verbale_riesame_direzione_compilabile.pdf`
- `MOD-07_checklist_freeze_release_accreditabile_compilabile.pdf`

## Rigenerazione

```bash
python3 scripts/generate_accredia_fillable_pdfs.py
```

I PDF generati sono A4, non criptati e contengono campi AcroForm editabili.
