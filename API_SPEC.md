# API_SPEC.md — Solidità 4.0

## Principi API

- REST JSON.
- Versioning `/api/v1`.
- Auth JWT.
- Tenant context obbligatorio.
- Error format standard.
- Upload immagini tramite signed URL oppure multipart controllato.
- Operazioni pesanti asincrone con job queue.

## Auth

### POST /api/v1/auth/login

Input:
```json
{
  "email": "operator@example.com",
  "password": "secret"
}
```

Output:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "companies": [
    {
      "id": "uuid",
      "name": "Tintoria Demo",
      "role": "lab_manager"
    }
  ]
}
```

### POST /api/v1/auth/refresh

Refresh token.

## Companies

### POST /api/v1/companies

Crea azienda.

### GET /api/v1/companies/me

Recupera tenant corrente.

### PATCH /api/v1/companies/{company_id}

Aggiorna configurazioni.

## Departments

### GET /api/v1/departments

Lista reparti.

### POST /api/v1/departments

Crea/attiva reparto.

Campi:
- Tintoria
- Stamperia Inkjet
- Stamperia Tradizionale
- Finissaggio/Confezione

## Devices

### POST /api/v1/devices/register

Registra iPhone autorizzato.

Input:
```json
{
  "hardware_uuid": "...",
  "model": "iPhone 16 Pro",
  "os_version": "iOS ...",
  "mdm_managed": true
}
```

### GET /api/v1/devices

Lista dispositivi.

### POST /api/v1/devices/{device_id}/calibrations

Carica profilo calibrazione.

## Brand Specifications

### GET /api/v1/brand-specifications

### POST /api/v1/brand-specifications

```json
{
  "brand_name": "Brand X",
  "rules": [
    {
      "test_method_code": "ISO_105_X12_WET",
      "fiber_code": "cotton",
      "max_delta_e": 1.0,
      "min_gray_scale_grade": 4.0,
      "severity": "blocking"
    }
  ]
}
```

## Batch Zero

### POST /api/v1/multifiber-batches

```json
{
  "batch_code": "MF-2026-001",
  "supplier": "Supplier",
  "reference_lab_values": {
    "acetate": {"L": 95.1, "a": 0.2, "b": 1.1},
    "cotton": {"L": 96.0, "a": 0.1, "b": 0.9},
    "nylon": {"L": 94.5, "a": 0.3, "b": 1.3},
    "polyester": {"L": 95.7, "a": 0.2, "b": 1.0},
    "acrylic": {"L": 96.2, "a": 0.1, "b": 0.8},
    "wool": {"L": 93.8, "a": 0.4, "b": 1.6}
  }
}
```

## Test Jobs

### POST /api/v1/test-jobs

Crea prova.

### GET /api/v1/test-jobs

Filtri:
- brand;
- test method;
- status;
- date range;
- pass/fail.

## Capture Sessions

### POST /api/v1/capture-sessions

Crea sessione acquisizione.

### POST /api/v1/capture-sessions/{id}/upload

Upload immagine.

### POST /api/v1/capture-sessions/{id}/analyze

Avvia analisi.

Output:
```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

## Results

### GET /api/v1/test-jobs/{id}/results

Ritorna risultati.

## Reports

### POST /api/v1/test-jobs/{id}/reports

Genera report PDF.

### GET /api/v1/reports

Certificate Ledger.

### GET /api/v1/reports/{id}/download

Signed URL PDF.

### GET /api/v1/reports/{id}/verify

Verifica hash.

## Hardware Kit Dispatch

### POST /api/v1/hardware-kits/dispatch-webhook

Webhook per trigger spedizione kit.

Input:
```json
{
  "company_id": "uuid",
  "kit_type": "vision_pro",
  "shipping_address": {},
  "include_iphone": true
}
```
