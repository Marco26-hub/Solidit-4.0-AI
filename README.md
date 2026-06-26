# Solidità 4.0 — Claude Production Pack

Questo pacchetto contiene la base tecnica, architetturale e operativa per sviluppare Solidità 4.0 con Claude Code o con un team tecnico.

## Obiettivo prodotto

Solidità 4.0 è una piattaforma SaaS multi-tenant per aziende tessili, tintorie, stamperie, laboratori interni e brand moda.

Il sistema digitalizza il controllo qualità tessile tramite:
- portale web amministrativo;
- app iPhone per acquisizione guidata;
- kit fisico di calibrazione;
- batch zero multifibra;
- specifiche brand;
- analisi immagine;
- DeltaE CIEDE2000;
- grey scale mapping configurabile;
- report PDF con hash SHA-256;
- audit ledger;
- storico qualità verificabile.

## Posizionamento corretto

Solidità 4.0 non deve essere venduto inizialmente come sostituto diretto di un laboratorio accreditato, ma come:

> Sistema digitale di controllo qualità tessile, tracciabilità, pre-validazione e standardizzazione interna.

## File inclusi

- PRODUCT_SPEC.md
- ARCHITECTURE.md
- DATABASE_SCHEMA.md
- API_SPEC.md
- VISION_ENGINE_SPEC.md
- MOBILE_APP_SPEC.md
- ADMIN_PORTAL_SPEC.md
- SECURITY_COMPLIANCE.md
- ROADMAP_SPRINT.md
- CLAUDE.md
- HANDOFF.md
- docs/quality/FASCICOLO_TECNICO.md
- docs/accredia/MANUALE_QUALITA_ISO17025.md
- docs/accredia/VALIDAZIONE_METODO_INGEGNERISTICA.md
- docs/accredia/MATRICE_REQUISITI_EVIDENZE.md
- docs/accredia/PROCEDURA_DOMANDA_ACCREDIA.md
- docs/accredia/MODULI_OPERATIVI.md
- output/pdf/accredia/Solidita_Accredia_Moduli_Compilabili.pdf

## Dossier Accredia / ISO 17025

Il dossier in `docs/accredia/` collega manuale qualita, validazione
ingegneristica, matrice evidenze, procedura domanda e moduli operativi.

Percorso consigliato:

1. usare `docs/accredia/MATRICE_REQUISITI_EVIDENZE.md` per la gap analysis;
2. compilare `docs/accredia/MODULI_OPERATIVI.md` con dati reali;
3. usare i PDF compilabili in `output/pdf/accredia/`;
4. seguire `docs/accredia/PROCEDURA_DOMANDA_ACCREDIA.md`;
5. congelare release software, algoritmo, kit hardware e profili grading;
6. validare con campioni reali e budget incertezza approvato.

Nota: la piattaforma supporta il laboratorio, ma non genera da sola
l'accreditamento. Restano necessari validazione reale, certificati, operatori
qualificati, audit interno, riesame direzione e moduli Accredia ufficiali.

## Nota importante

Le formule/tabelle ufficiali ISO/AATCC possono essere coperte da copyright o accesso a pagamento. Il sistema deve prevedere un motore configurabile dove caricare coefficienti, soglie e regole validate internamente o licenziate dal cliente/laboratorio.
