# MediVault Security Model

## Objective

MediVault handles highly sensitive healthcare information. The security architecture therefore follows defense-in-depth and zero-trust principles.

## Authentication

Authentication should be handled through Supabase Auth. The backend must validate authenticated identity before performing protected operations.

Authentication establishes identity; authorization determines what that identity is allowed to access.

## Authorization

Every protected record operation must verify the authenticated user, role, patient ownership, requested resource, active consent where applicable, sharing scope, expiration, and revocation status.

Frontend route guards are not sufficient authorization.

## Row Level Security

PostgreSQL Row Level Security should protect patient-owned records. A patient must not be able to query another patient's records even if an application-layer check is bypassed.

## Private Storage

Medical documents must reside in private storage buckets. Public URLs must not be used for medical records. Access should use short-lived signed URLs or an authorized backend endpoint.

## Encryption

Use TLS for network communication and the encryption capabilities of the managed database and storage infrastructure. Application secrets must never be stored in Git.

## Audit Logging

Sensitive operations should generate append-oriented audit events containing, where appropriate: event ID, timestamp, actor ID, actor role, patient ID, resource ID, action, outcome, IP address, user agent, and request/correlation ID.

Examples include `RECORD_VIEW`, `RECORD_DOWNLOAD`, `DOCUMENT_UPLOAD`, `DOCUMENT_DELETE`, `SHARE_CREATED`, `SHARE_REVOKED`, and `ACCESS_DENIED`.

## AI Safety

The AI extraction layer must not be presented as a diagnostic system. It may extract information explicitly present in a document, including stated diagnoses, medications, laboratory values, vital signs, hospitals, physicians, dates, and procedures.

It must not invent diagnoses, treatments, recommendations, or missing medical facts. If information is absent or ambiguous, preserve uncertainty rather than guessing.

## Threat Model

MediVault should consider stolen credentials, unauthorized record enumeration, IDOR vulnerabilities, leaked document URLs, compromised API credentials, malicious uploads, prompt injection in documents, compromised AI providers, replayed sharing tokens, excessive doctor permissions, insider access, database misconfiguration, and exposed environment variables.

## Security Principle

Authentication, authorization, RLS, private storage, scoped sharing, and audit logging should operate together. No single mechanism should be treated as the only security boundary.
