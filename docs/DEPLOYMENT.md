# MediVault Deployment Architecture

## Prototype

```text
Browser
  |
  v
Frontend
  |
  v
FastAPI
  +--> Supabase Auth
  +--> PostgreSQL + RLS
  +--> Private Storage
  +--> OCR Provider
  +--> LLM Provider
```

## Environment Variables

Secrets must be supplied through the deployment environment. Never commit API keys, JWT secrets, database passwords, service-role keys, OAuth secrets, or cloud credentials.

## Frontend

The browser should contain only public configuration required by the client. Privileged Supabase service credentials must never be exposed to the browser.

## Backend

FastAPI should hold server-side AI provider credentials, signing keys, and other privileged service credentials.

## Background Processing

The SIH prototype may use FastAPI background tasks. A larger deployment should use a durable queue and dedicated workers:

```text
API -> Job Queue -> OCR Worker
                 -> Extraction Worker
                 -> Validation Worker
```

## Observability

Monitor API errors, authentication failures, processing failures, OCR failures, LLM failures, queue latency, storage failures, and unauthorized access attempts. Logs must not contain unnecessary medical information.

## Backup and Recovery

Backups should cover the database and required document storage. Recovery procedures should be tested rather than merely documented.

## Production Readiness

Before production healthcare use, MediVault requires a formal security, privacy, regulatory, threat-model, and operational review. The SIH prototype must clearly distinguish prototype capabilities from production compliance or certification claims.
