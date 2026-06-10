# ARCHITECTURE.md — Solidità 4.0

## Architettura generale

```
Mobile App iPhone
    |
    | barcode, immagini, telemetria, sensori
    v
FastAPI Backend
    |
    +--> Auth Service
    +--> Tenant Service
    +--> Device Registry
    +--> Calibration Service
    +--> Capture Session Service
    +--> Vision Engine
    +--> Standards Mapping Engine
    +--> Brand Rules Engine
    +--> Report Service
    +--> Audit Ledger
    |
PostgreSQL + Object Storage + Worker Queue
    |
React Admin Portal
```

## Componenti

### 1. Backend API

Stack:
- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2
- Alembic
- PostgreSQL
- Redis
- Celery/RQ/Arq per worker async
- S3-compatible object storage

Responsabilità:
- gestione tenant;
- utenti;
- ruoli;
- dispositivi;
- sessioni acquisizione;
- immagini;
- elaborazioni;
- report;
- audit;
- API mobile e web.

### 2. Database

PostgreSQL con:
- Row Level Security;
- UUID primarie;
- JSONB per telemetrie e risultati;
- audit log append-only;
- viste per dashboard;
- indici GIN su JSONB dove necessario.

### 3. Vision Engine

Stack:
- OpenCV;
- scikit-image;
- numpy;
- scipy;
- Pillow;
- optional: ONNX Runtime / CoreML export later.

Pipeline:
1. validate capture;
2. detect markers;
3. perspective correction via homography;
4. ROI extraction;
5. color correction via calibration matrix/LUT;
6. RGB to Lab;
7. DeltaE CIEDE2000;
8. grey scale mapping;
9. brand rule evaluation;
10. result persistence.

### 4. Mobile App

Stack consigliato:
- React Native;
- TypeScript;
- native modules iOS per camera/sensori se necessario;
- barcode scanning;
- offline queue;
- secure storage.

Funzioni:
- login operatore;
- selezione azienda/reparto;
- scan barcode;
- workflow test;
- acquisizione guidata;
- sensori;
- upload;
- anteprima result.

### 5. Admin Portal

Stack:
- React;
- TypeScript;
- Tailwind CSS;
- TanStack Query;
- React Hook Form;
- Zod;
- Vite/Next.js.

Funzioni:
- dashboard aziende;
- brand spec manager;
- batch zero registry;
- device manager;
- certificate ledger;
- report viewer;
- export.

### 6. Object Storage

Salvare:
- raw images;
- corrected images;
- ROI crops;
- PDFs;
- thumbnails;
- calibration assets.

### 7. Report Service

Genera PDF con:
- dati prova;
- risultati;
- immagini;
- hash SHA-256;
- QR di verifica;
- algoritmo/versione;
- disclaimer.

### 8. Security Layer

- JWT access/refresh;
- password hashing;
- MFA opzionale;
- tenant-aware sessions;
- RLS enforcement;
- audit log;
- object storage signed URLs;
- encryption at rest;
- backup.

## Environments

- local;
- staging;
- production.

## Deployment target

Prima fase:
- Docker Compose per sviluppo;
- VPS/Cloud con PostgreSQL managed;
- S3-compatible storage;
- GitHub Actions CI/CD.

Fase enterprise:
- Kubernetes opzionale;
- managed Redis;
- managed observability;
- multi-region backup.
