# MOBILE_APP_SPEC.md — Solidità 4.0 Mobile

## Stack consigliato

- React Native
- TypeScript
- Native iOS modules dove necessario
- Camera module
- Barcode scanner
- Secure storage
- Offline queue
- API client typed

## Hardware minimo

- iPhone 16 Pro o superiore consigliato.
- iPhone 15 Pro/Pro Max compatibile previa calibrazione.
- Modelli non Pro solo per consultazione/report/barcode, non per acquisizione Vision.

## UX principale

```
Login
 -> Seleziona azienda/reparto
 -> Scansiona barcode commessa
 -> Scegli test
 -> Inserisci campione nella dima
 -> App valida condizioni
 -> Scatto automatico
 -> Upload
 -> Risultato preliminare
 -> Report/ledger
```

## Schermate

### 1. LoginScreen

- email;
- password;
- tenant selector.

### 2. DepartmentSelectorScreen

- Tintoria;
- Stamperia Inkjet;
- Stamperia Tradizionale;
- Finissaggio/Confezione.

### 3. BarcodeScanScreen

- scan codice articolo/commessa;
- fetch brand specs;
- fetch test target.

### 4. WorkflowSelectorScreen

Gruppi:

#### Predictive Vision

- Ink-load crocking risk;
- fixation/steaming optimization index.

#### Instrumental ISO/AATCC Proofs

- wash;
- rubbing/crocking;
- sweat;
- shrinkage;
- yarn slippage;
- pilling.

#### Real-time Edge Video

- rouloté inspection;
- weaving defect mapping.

### 5. GuidedCaptureScreen

Overlay:
- bounding box multifibra;
- bounding box tile/reference card;
- marker corners;
- distance indicator;
- tilt indicator;
- blur indicator;
- exposure indicator.

La cattura manuale deve essere bloccata nella modalità metrologica. Lo scatto avviene solo quando:
- inclinazione OK;
- distanza OK;
- blur OK;
- exposure OK;
- marker OK;
- tile OK.

## Nota sensori

La distanza deve essere garantita principalmente dalla dima fisica. LiDAR/ToF è solo controllo di coerenza.

## Stato app

Usare store centralizzato:

```ts
type CaptureState = {
  companyId: string;
  departmentId: string;
  deviceId: string;
  testJobId: string;
  selectedWorkflow: string;
  telemetry: {
    tiltDeg: number;
    distanceMm?: number;
    blurScore: number;
    exposureScore: number;
    motionScore: number;
  };
  captureReady: boolean;
  errors: string[];
};
```

## Offline mode

Se rete assente:
- salvare capture criptata localmente;
- mostrare pending upload;
- inviare appena online;
- bloccare generazione report finale se non sincronizzato.

## MDM / Device Ready

Se il cliente acquista iPhone configurato:
- app preinstallata;
- profilo dispositivo;
- restrizioni aggiornamenti;
- account aziendale;
- tenant già associato;
- device UUID registrato;
- calibrazione iniziale caricata.

## Sicurezza mobile

- token in secure storage;
- refresh token rotation;
- no dati sensibili in log;
- upload firmato;
- blocco screenshot opzionale;
- logout remoto per device revocato.
