# Manuale Qualita ISO/IEC 17025 - Solidita 4.0

> Stato: DRAFT controllato. Non usare come manuale approvato senza riesame del
> Responsabile Qualita, Direzione del laboratorio e consulente ISO/IEC 17025.

## 1. Identificazione

| Campo | Valore |
|---|---|
| Organizzazione | Da compilare |
| Laboratorio | Da compilare |
| Metodo/software | Solidita 4.0 |
| Versione documento | 0.1 |
| Responsabile qualita | Da compilare |
| Responsabile tecnico | Da compilare |
| Approvazione direzione | Da compilare |

## 2. Posizionamento e campo di applicazione

Solidita 4.0 e una piattaforma di controllo qualita tessile digitale per
tracciabilita, pre-validazione, standardizzazione interna, acquisizione immagini,
calcolo assistito e reportistica.

Il sistema non deve essere presentato come sostituto automatico di un laboratorio
accreditato, spettrofotometro o colorimetro certificato. Nel perimetro di un
laboratorio ISO/IEC 17025 puo essere usato come metodo/software validato per uno
scopo definito, con kit hardware controllato, operatori qualificati, riferimenti
certificati, incertezza stimata e validazione contro metodo di riferimento.

## 3. Scopo di accreditamento proposto

Lo scopo deve essere ristretto e verificabile. Esempio di formulazione da
riesaminare:

| Campo | Proposta |
|---|---|
| Settore | Tessile / controllo solidita colore |
| Oggetto prova | Campioni tessili opachi, non fluorescenti, non metallizzati |
| Metodi identificativi | ISO 105 applicabili, solo come identificativo/licenza cliente |
| Measurand | DeltaE CIEDE2000 e/o grado scala grigi assistito |
| Tecnologia | Imaging RGB lineare caratterizzato, lightbox controllata, dima, riferimenti certificati |
| Esclusioni | Metamerismo multi-illuminante, UV/sbiancanti ottici, gloss, effetti metallici, campioni traslucidi |

## 4. Imparzialita e indipendenza

Il laboratorio deve:

- identificare rischi di pressione commerciale sui risultati;
- separare responsabilita tecnica e commerciale quando possibile;
- registrare eventuali conflitti di interesse;
- impedire modifiche non autorizzate ai risultati finalizzati;
- vietare claim di accreditamento su prove fuori scopo.

Evidenze richieste:

- registro rischi imparzialita;
- nomina responsabili;
- audit su almeno un ciclo completo di prova;
- controllo accessi e ruoli in Solidita 4.0.

## 5. Riservatezza e sicurezza dati

I dati gestiti includono articoli, brand specification, lotti, immagini, risultati
di prova, report PDF, operatori e audit trail.

Controlli minimi:

- autenticazione individuale;
- ruoli e tenant isolation;
- PostgreSQL Row Level Security;
- audit trail append-only;
- storage immagini/report con accesso controllato;
- backup e test di restore;
- retention definita contrattualmente;
- trattamento GDPR documentato.

Evidenze software:

- RLS abilitata e forzata sulle tabelle tenant-scoped;
- report con hash SHA-256;
- report finalizzato/locked non riemesso;
- log audit per azioni critiche.

## 6. Organizzazione e responsabilita

| Ruolo | Responsabilita |
|---|---|
| Direzione laboratorio | Risorse, approvazione sistema qualita, riesame |
| Responsabile qualita | Manuale, SOP, audit, NC, riesame, documenti Accredia |
| Responsabile tecnico | Validazione metodo, incertezza, attrezzature, personale tecnico |
| Operatore | Acquisizione, esecuzione prova, registrazioni |
| Amministratore software | Account, versioni, configurazione, backup |
| Consulente ISO 17025 | Riesame indipendente, gap analysis, preparazione domanda |

## 7. Gestione documenti

Ogni documento deve avere:

- codice;
- titolo;
- versione;
- data;
- autore;
- approvatore;
- stato: draft, in revisione, approvato, ritirato;
- elenco modifiche.

Documenti principali:

- manuale qualita;
- SOP operative;
- piano validazione;
- rapporto validazione;
- budget incertezza;
- registro strumenti;
- registro formazione;
- registro NC;
- registro versioni software;
- riesame direzione;
- audit interni.

## 8. Riesame richieste, offerte e contratti

Prima di accettare una prova, il laboratorio verifica:

- metodo richiesto e scopo applicabile;
- campione idoneo al metodo imaging;
- limiti dichiarati al cliente;
- disponibilita kit hardware valido;
- disponibilita operatori qualificati;
- eventuale necessita di laboratorio esterno;
- uso previsto del report.

Output:

- accettazione prova;
- rifiuto motivato;
- esecuzione come pre-validazione non accreditata;
- invio a laboratorio esterno/partner.

## 9. Selezione e validazione metodi

Il metodo digitale deve essere trattato come metodo non normalizzato o metodo
normalizzato con applicazione software/strumentale specifica, a seconda dello
scopo finale concordato con il consulente.

Regole:

- non copiare testo o tabelle proprietarie ISO/AATCC;
- usare norme solo come identificativo e licenze del laboratorio/cliente;
- documentare ogni deviazione dal metodo tradizionale;
- validare ogni famiglia di prova nello scopo;
- non estendere risultati a materiali/illuminanti non validati.

Riferimento operativo:

- `VALIDAZIONE_METODO_INGEGNERISTICA.md`
- `docs/quality/SOP_06_validazione.md`

## 10. Attrezzature e riferibilita metrologica

Kit minimo per analisi Vision validabile:

- iPhone/dispositivo identificato;
- app nativa per cattura controllata;
- dima/cornice con geometria controllata;
- lightbox verificata;
- scala grigia fisica idonea;
- piastrina bianca certificata;
- target colore/ColorChecker per caratterizzazione;
- eventuale spettrofotometro/colorimetro di riferimento o laboratorio esterno.

Regole:

- ogni riferimento ha codice, certificato, validita e stato;
- analisi software bloccata se manca il kit richiesto;
- analisi bloccata se riferimento scaduto/dismesso;
- riferibilita documentata tramite certificati;
- verifiche intermedie pianificate.

## 11. Ambiente e condizioni di prova

Condizioni da controllare:

- illuminante lightbox;
- ore lampada/stato LED;
- riflessi e ombre;
- planarita campione;
- temperatura/umidita se rilevanti per il metodo;
- distanza/crop fissati da dima;
- orientamento striscia e ordine fibre.

Le condizioni devono essere registrate o rese ripetibili dal kit.

## 12. Personale e qualifica

Ogni operatore deve essere formato su:

- limiti del metodo;
- SOP di acquisizione;
- gestione kit;
- riconoscimento catture non valide;
- gestione warning;
- finalizzazione report;
- non conformita.

Qualifica minima:

- esecuzione supervisionata di prove pilota;
- confronto con risultati di riferimento;
- autorizzazione documentata dal Responsabile Tecnico;
- riqualifica dopo cambio metodo/software/hardware.

## 13. Assicurazione validita dei risultati

Controlli richiesti:

- repeatability su repliche;
- reproducibility fra operatori/sessioni;
- campioni di controllo periodici;
- trend su bias/RMSE;
- PT/ILC quando disponibile;
- audit di report finalizzati;
- riesame warning e non conformita.

Indicatori minimi:

- % entro tolleranza;
- bias;
- RMSE;
- scarto massimo;
- incertezza estesa U;
- tasso catture rifiutate;
- tasso report riemessi/bloccati.

## 14. Incertezza di misura

Il laboratorio deve mantenere un budget d'incertezza per ogni scopo/metodo
validato.

Componenti minime:

- repeatability;
- reproducibility;
- characterisation residual;
- reference standard/certificate;
- eventuale risoluzione/quantizzazione;
- drift lightbox/target;
- contributo operatore se significativo.

Metodo:

- convertire ogni componente in incertezza standard;
- combinare in quadratura;
- stimare gradi di liberta effettivi quando disponibili;
- calcolare incertezza estesa;
- applicare regola decisionale con guard band per pass/fail.

Il modulo `Colorimetria -> Budget incertezza` supporta questo calcolo.

## 15. Regola decisionale

La conformita deve considerare l'incertezza. Regola consigliata:

- limite massimo: PASS solo se `valore + U <= limite`;
- limite minimo: PASS solo se `valore - U >= limite`;
- se l'intervallo attraversa il limite: risultato borderline/inconclusivo o
  richiesta conferma con metodo di riferimento.

La regola deve essere comunicata al cliente prima della prova.

## 16. Report e uso claim

Il report Solidita contiene:

- dati prova;
- risultati;
- provenienza;
- riferimenti;
- warning;
- hash SHA-256;
- verifica pubblica;
- stato finalizzato/locked.

Regole:

- SHA-256 e sigillo di integrita, non firma qualificata;
- nessun uso logo Accredia prima di accreditamento;
- nessun claim accreditato su prove fuori scopo;
- disclaimer obbligatorio per pre-validazione/non accreditato.

## 17. Non conformita e azioni correttive

Non conformita tipiche:

- kit mancante o scaduto;
- cattura rifiutata;
- warning ignorato;
- profilo grading esempio usato in report cliente;
- scostamento eccessivo da riferimento;
- cambio software senza ri-verifica;
- report errato finalizzato.

Ogni NC richiede:

- registrazione;
- impatto;
- contenimento;
- causa radice;
- azione correttiva;
- verifica efficacia;
- chiusura approvata.

## 18. Audit interni

Frequenza minima: annuale o prima della domanda Accredia.

Audit trail minimo:

- una prova completa da accettazione a report;
- gestione strumento scaduto;
- validazione metodo;
- calcolo incertezza;
- formazione operatore;
- backup/restore;
- sicurezza accessi.

## 19. Riesame direzione

Input:

- risultati audit;
- NC;
- reclami;
- KPI validazione;
- PT/ILC;
- cambi software/hardware;
- stato formazione;
- opportunita e rischi.

Output:

- decisioni;
- risorse;
- azioni;
- revisione scopo;
- approvazione o blocco uso operativo.

## 20. Prerequisiti prima della domanda Accredia

- Manuale e SOP approvati.
- Scopo di accreditamento definito.
- Kit hardware completo con certificati.
- Dataset validazione reale.
- Rapporto validazione approvato.
- Budget incertezza approvato.
- Evidenze operatori qualificati.
- PT/ILC o giustificazione.
- Audit interno chiuso.
- Riesame direzione completato.
- Moduli Accredia ufficiali compilati.

