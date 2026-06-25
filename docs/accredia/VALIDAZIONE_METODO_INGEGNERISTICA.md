# Validazione Metodo Ingegneristica - Solidita 4.0

> Stato: DRAFT tecnico. Obiettivo: dimostrare, con dati reali, che il metodo
> digitale produce risultati idonei allo scopo dichiarato. Non e una promessa di
> accreditamento automatico.

## 1. Obiettivo

Validare il metodo Solidita 4.0 per valutazione assistita della solidita colore
tramite imaging digitale controllato.

Il metodo da validare include:

1. acquisizione con kit hardware;
2. controllo qualita immagine;
3. correzione geometrica;
4. correzione colore;
5. conversione RGB lineare/caratterizzato -> CIELAB;
6. calcolo DeltaE CIEDE2000;
7. mapping DeltaE -> grado scala grigi;
8. confronto con regole brand/metodo;
9. report con provenienza e incertezza.

## 2. Ipotesi da dimostrare

H1: entro lo scopo definito, Solidita 4.0 produce gradi/DeltaE coerenti con il
metodo di riferimento entro la tolleranza stabilita.

H2: il metodo e ripetibile nello stesso setup operatore/strumento.

H3: il metodo e riproducibile fra operatori/sessioni entro una soglia definita.

H4: l'incertezza combinata e compatibile con la decisione pass/fail.

H5: i casi fuori scopo o non idonei sono intercettati da gate, warning o blocco.

## 3. Scopo tecnico validabile

Definire prima dei test:

| Campo | Decisione richiesta |
|---|---|
| Metodo/i prova | Es. ISO 105-X12, ISO 105-E04, ecc. |
| Tipo valutazione | Staining, colour-change o entrambi |
| Materiali | Fibra/tessuto, esclusioni |
| Illuminante | D65/TL84/altro |
| Strumento riferimento | Spettrofotometro, colorimetro, laboratorio esterno, panel esperto |
| Output primario | DeltaE, grado scala grigi, pass/fail |
| Tolleranza | Es. +/-0.5 grado o limite DeltaE |
| Decision rule | Guard band con incertezza estesa |

## 4. Architettura sperimentale

### 4.1 Fase 0 - Prerequisiti

Prima di acquisire campioni:

- kit hardware registrato;
- lightbox valida;
- scala grigia valida;
- white tile valida;
- ColorChecker/target valido;
- operatori formati;
- versione software congelata;
- piano validazione approvato;
- profili grading definiti e tracciati;
- metodo riferimento definito.

### 4.2 Fase 1 - Studio pilota

Obiettivo: scoprire problemi prima del dataset ufficiale.

Campioni minimi:

- 10-15 campioni;
- colori chiari, medi, scuri, saturi;
- almeno 2 livelli di staining/change;
- 2 operatori;
- 2 sessioni.

Output:

- verifica workflow;
- revisione SOP;
- identificazione failure mode;
- prima stima repeatability.

Questa fase non sostituisce la validazione ufficiale.

### 4.3 Fase 2 - Validazione principale

Campioni minimi consigliati:

- 50 campioni per pre-validazione;
- 100 campioni per robustezza;
- almeno 3 operatori se il metodo e usato da piu operatori;
- almeno 3 giorni/sessioni;
- almeno 2 dispositivi se si vogliono coprire piu device.

Stratificazione:

| Dimensione | Livelli minimi |
|---|---|
| Colore | chiaro, medio, scuro, saturo, neutro |
| Materiale | cotone, poliammide, poliestere, acrilico/lana se nello scopo |
| Intensita effetto | nullo, basso, medio, alto |
| Texture | liscia, trama visibile, pelo/superficie critica |
| Metodo | ogni famiglia nello scopo |

### 4.4 Fase 3 - Robustezza

Variare controllatamente:

- operatore;
- giorno;
- dispositivo;
- lightbox;
- posizione campione;
- lieve rotazione entro dima;
- esposizione entro gate accettabili.

Il metodo deve mantenere risultati entro i criteri definiti o bloccare/avvisare.

## 5. Disegno di misura

Per ogni campione:

1. assegnare ID cieco;
2. misurare con metodo di riferimento;
3. acquisire con Solidita 4.0;
4. ripetere N acquisizioni;
5. ripetere con secondo operatore/sessione;
6. registrare strumenti e ambiente;
7. congelare dati raw e risultati.

### Repliche minime

| Studio | Repliche |
|---|---|
| Repeatability | 3-5 acquisizioni stesso operatore/sessione |
| Reproducibility | 2-3 operatori x 2 sessioni |
| Device comparison | 2 dispositivi, stesso campione/setup |
| Drift | campione controllo a inizio/fine giornata |

## 6. Metodo di riferimento

Opzioni, in ordine di forza:

1. laboratorio esterno accreditato;
2. spettrofotometro/colorimetro tarato con procedura documentata;
3. panel visivo esperto secondo procedura documentata;
4. storico interno, solo per screening.

Il riferimento deve avere:

- identificazione strumento/lab;
- certificato/taratura;
- incertezza o ripetibilita nota;
- condizioni di misura;
- operatore;
- data.

## 7. Metriche da calcolare

### 7.1 Metriche per grado scala grigi

- errore assoluto medio in gradi;
- % entro +/-0.5 grado;
- % entro +/-1.0 grado;
- bias medio;
- RMSE;
- max error;
- confusion matrix per classi di grado;
- tasso borderline.

### 7.2 Metriche per DeltaE

- bias DeltaE;
- RMSE DeltaE;
- errore assoluto mediano;
- p95 errore;
- Bland-Altman;
- regressione Solidita vs riferimento;
- outlier analysis.

### 7.3 Repeatability

Per ogni campione:

- deviazione standard DeltaE;
- range grado;
- max deviation grade;
- coefficient of variation se utile.

Aggregato:

- media sd;
- p95 sd;
- % campioni con scarto <= 0.5 grado.

### 7.4 Reproducibility

Analisi per operatore/sessione:

- ANOVA o mixed effects se disponibile;
- differenza media fra operatori;
- p95 differenza;
- outlier per operatore.

### 7.5 MSA / Gage R&R

Per un set rappresentativo:

- repeatability component;
- reproducibility component;
- part-to-part variation;
- %GRR;
- ndc se applicabile.

Per metodo di grading discreto, integrare con concordanza:

- Cohen/Fleiss kappa pesata;
- % agreement entro +/-0.5 grado.

## 8. Criteri di accettazione

Da approvare prima della validazione. Proposta iniziale:

| Indicatore | Criterio indicativo |
|---|---|
| Campioni entro +/-0.5 grado | >= 90% pre-validazione, >= 95% robusta |
| Bias grado | <= 0.25 grado |
| RMSE grado | <= 0.5 grado |
| Max errore | investigare se > 1 grado |
| Repeatability | p95 scarto <= 0.5 grado |
| Reproducibility | p95 differenza <= 0.5 grado |
| Catture rifiutate | motivate, non aggirate |
| Outlier | causa radice documentata |

Se il metodo produce risultati borderline rispetto a capitolato, applicare la
regola decisionale con incertezza.

## 9. Incertezza di misura

### 9.1 Componenti minime

| Componente | Tipo | Fonte |
|---|---|---|
| Repeatability | A | repliche stesso setup |
| Reproducibility | A | operatori/sessioni/device |
| Characterisation | A/B | RMS DeltaE ColorChecker fit |
| Reference | B | certificato strumento/lab |
| Drift | A/B | campione controllo |
| Resolution/grading | B | discretizzazione scala |

### 9.2 Calcolo

1. Convertire ogni componente in incertezza standard.
2. Usare distribuzione appropriata:
   - normale per sd osservate;
   - rettangolare per limiti/certificati senza distribuzione;
   - triangolare per valori piu probabili al centro;
   - u-shaped solo se giustificata.
3. Combinare in quadratura.
4. Calcolare gradi di liberta effettivi se disponibili.
5. Calcolare U estesa.
6. Applicare guard band.

Il modulo `Colorimetria -> Budget incertezza` implementa questi calcoli.

## 10. Validazione software

### 10.1 Requisiti software critici

- isolamento tenant/RLS;
- audit trail;
- blocco hardware calibration;
- blocco riferimenti scaduti;
- versionamento algoritmo;
- report locked;
- hash report;
- provenienza completa;
- warning non nascosti.

### 10.2 Test richiesti

- unit test conversione Lab/DeltaE;
- test caratterizzazione;
- test incertezza;
- test hardware gate;
- test report hash;
- test RLS tenant;
- test locked report;
- test regressione su dataset fisso.

### 10.3 Change control

Ogni modifica che impatta risultato richiede:

- changelog tecnico;
- riesecuzione dataset regressione;
- confronto prima/dopo;
- approvazione Responsabile Tecnico;
- aggiornamento `algorithm_version` se necessario.

## 11. Failure mode analysis

| Failure mode | Controllo |
|---|---|
| Kit mancante | blocco API/UI |
| Reference scaduta | blocco `reference_invalid` |
| RGB non lineare usato per caratterizzazione | SOP + controllo training |
| Campione lucido/metallizzato | fuori scopo o metodo alternativo |
| Sbiancante ottico/UV | fuori scopo se non validato |
| Profilo grading esempio | warning, vietato in uso accreditato |
| Cattura sfocata/sovraesposta | strict quality gate |
| Operatore non formato | blocco procedurale |
| Drift lightbox | verifiche intermedie |

## 12. Dataset e tracciabilita

Ogni record validazione deve contenere:

- sample_id;
- materiale;
- colore;
- metodo;
- riferimento usato;
- risultato riferimento;
- risultato Solidita;
- operatore;
- device;
- lightbox;
- grey scale;
- white tile;
- target colore;
- versione software;
- immagine raw/hash;
- warning;
- note/outlier.

I dati raw non devono essere sovrascritti.

## 13. Rapporto validazione

Il rapporto deve includere:

- scopo;
- versione software;
- hardware;
- riferimenti;
- dataset;
- criteri accettazione;
- risultati metriche;
- outlier e cause;
- incertezza;
- decisione finale;
- limitazioni;
- firma Responsabile Tecnico e Qualita.

Esito possibile:

- approvato per scopo definito;
- approvato con limitazioni;
- non approvato;
- necessita ulteriore campionamento.

## 14. Decisione di rilascio

Il metodo puo passare da pre-validazione a uso controllato solo se:

- criteri principali rispettati;
- budget incertezza approvato;
- nessun outlier critico irrisolto;
- SOP approvate;
- operatori qualificati;
- kit e riferibilita completi;
- audit interno completato.

## 15. Piano operativo suggerito

### Sprint A - Preparazione

- congelare versione software;
- definire scopo;
- approvare piano;
- preparare kit e certificati;
- formare operatori.

### Sprint B - Pilota

- 10-15 campioni;
- 2 operatori;
- correzione SOP;
- correzione failure mode.

### Sprint C - Validazione

- 50-100 campioni;
- reference lab/spettrofotometro;
- repeatability/reproducibility;
- calcolo incertezza;
- rapporto.

### Sprint D - Pre-audit

- audit interno;
- riesame direzione;
- compilazione moduli Accredia;
- gap closure.

## 16. Criterio di stop

Bloccare uso accreditabile se:

- kit incompleto;
- reference scaduta;
- dataset insufficiente;
- bias fuori criterio;
- incertezza incompatibile con decisione;
- software non congelato;
- profili grading non validati/licenziati;
- operatori non qualificati.

