# MediVault Architecture

## Overview

MediVault is a patient-controlled digital health record platform designed to securely collect, preserve, structure, and share medical information.

The architecture separates presentation, application services, persistent healthcare data, document storage, and AI/OCR processing.

## Architecture

```text
Browser
  |
  v
Next.js / React + Tailwind
  |
  v
FastAPI Application Layer
  |       |        |        |
  v       v        v        v
Auth   PostgreSQL Storage  AI/OCR
         + RLS             Pipeline
  |
  v
FHIR-compatible healthcare model
```

## Core Components

### Frontend

The frontend provides patient authentication, patient dashboard, lifelong medical timeline, medical-document upload, extracted-record review, doctor access, consent management, and access-log visualization.

### FastAPI Backend

FastAPI is the application boundary between the frontend, database, storage, and intelligence services. Responsibilities include authentication validation, authorization, record operations, secure upload URL generation, document processing orchestration, OCR, AI extraction, FHIR transformation, sharing-token management, consent enforcement, and audit logging.

### Supabase

Supabase provides PostgreSQL, authentication, Row Level Security, and private object storage.

Healthcare records must never depend solely on frontend authorization. Authorization must ultimately be enforced server-side and at the database layer.

## Document Processing

```text
Patient
  |
  v
Secure Upload
  |
  v
Private Storage
  |
  v
Processing Job
  |
  v
OCR
  |
  v
Raw Extracted Text
  |
  v
Structured LLM Extraction
  |
  v
Validation
  |
  v
FHIR-Compatible Data
  |
  v
PostgreSQL
  |
  v
Patient Timeline
```

## Architectural Principles

1. Patient data ownership comes first.
2. Raw documents remain preserved.
3. AI extracts stated information; it does not diagnose.
4. Every sensitive access is auditable.
5. Sharing is explicit, scoped, and time-bound.
6. Revocation must be enforceable independently of token expiration.
7. Database authorization must not depend on frontend behavior.
8. Healthcare data should use interoperable standards where practical.
9. External AI providers should receive only the minimum data required.
10. Secrets must never be committed to source control.
