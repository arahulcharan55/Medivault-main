# MediVault

**A patient-controlled digital health record platform** — upload medical documents, extract structured records, build a timeline, and share with doctors via explicit consent.

[![License: Apache 2.0](LICENSE)](LICENSE)

## Quick Start (Local)

```bash
# 1. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=. python scripts/seed_demo.py
uvicorn app.main:app --reload --port 8000

# 2. Frontend (new terminal)
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Or use the helper script:

```bash
chmod +x scripts/start-local.sh
./scripts/start-local.sh
```

Open **http://localhost:3000**

### Demo accounts

| Role | Email | Password |
|------|-------|----------|
| Patient | `patient@demo.medivault` | `password123` |
| Doctor | `doctor@demo.medivault` | `password123` |

Upload `samples/demo-lab-report.pdf` as the patient, then create a consent grant for the doctor.

## What's Implemented

| Component | Status |
|-----------|--------|
| FastAPI backend with JWT auth | ✅ |
| Patient / doctor registration & login | ✅ |
| Document upload + private local storage | ✅ |
| Duplicate-hash detection + extraction review | ✅ |
| OCR/extraction pipeline (named labs, vitals, meds, allergies) | ✅ |
| Health summary + abnormal-value flags | ✅ |
| FHIR R4 collection bundle export | ✅ |
| Medical timeline with search/filters | ✅ |
| Scoped consent grants + revocation | ✅ |
| Doctor portal (timeline, documents, summary) | ✅ |
| Append-only audit logging | ✅ |
| Next.js frontend | ✅ |

## Architecture

```text
Next.js UI → FastAPI API → SQLite (local) / PostgreSQL (production)
                         → Local storage (dev) / Supabase storage (prod)
                         → Mock OCR/LLM (dev) / Cloud providers (prod)
```

**Security boundaries enforced server-side:** authentication, authorization, consent scope, revocation, and audit logging. The frontend is not the security boundary.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/README.md](docs/README.md).

## API

- Swagger UI: http://localhost:8000/docs
- Base URL: `http://localhost:8000/v1`

## Project Status

This is a **working SIH prototype**. It uses SQLite and local file storage for zero-config local development. Production deployment should migrate to Supabase PostgreSQL + RLS + private buckets per the architecture docs.

**Not claimed:** ABDM certification, regulatory compliance, clinical validation, production readiness.

## Disclaimer

MediVault is a software prototype and does **not** provide medical diagnosis or medical advice. AI extraction is assistive only — verify against original documents.

## Documentation

Full specification: [docs/README.md](docs/README.md)

## License

Apache 2.0
