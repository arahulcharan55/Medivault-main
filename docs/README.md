# MediVault Documentation

> **August 2026:** Working SIH prototype with FastAPI backend + Next.js frontend. Local dev uses SQLite and filesystem storage; production target is Supabase + PostgreSQL RLS.

## Start Here

- [ARCHITECTURE.md](./ARCHITECTURE.md) — System overview
- [HOW-IT-WORKS.md](./HOW-IT-WORKS.md) — Lifecycle (planned doc; see README for current flow)
- [SECURITY.md](./SECURITY.md) — Security model
- [ACCESS-CONTROL.md](./ACCESS-CONTROL.md) — Consent & authorization
- [AI-OCR-PIPELINE.md](./AI-OCR-PIPELINE.md) — Processing pipeline
- [DATA-MODEL.md](./DATA-MODEL.md) — Entities
- [DEPLOYMENT.md](./DEPLOYMENT.md) — Deployment notes

## Local Development

See root [README.md](../README.md) and [DEVELOPMENT.md](./DEVELOPMENT.md).

## Principles

- AI is **not** the source of truth
- Frontend is **not** the security boundary
- JWT proves identity; **consent grants** prove authorization
- FHIR-ready ≠ ABDM certified
