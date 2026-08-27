# MediVault Access Control

## Principle

MediVault uses patient-controlled, least-privilege access. A doctor does not automatically receive a patient's complete medical history. Access must be explicitly granted.

## Sharing Flow

```text
Patient -> Select Records/Scope -> Select Doctor -> Set Expiration
        -> Create Share Grant -> Short-Lived Access Token -> Doctor Portal
```

## Share Grant

```text
 grant_id
 patient_id
 doctor_id
 scope
 issued_at
 expires_at
 revoked_at
 token_identifier
 status
```

## Token Design

Tokens should be short-lived, signed, scoped, and bound to the intended share grant. The server must not trust a client-provided patient or record identifier simply because it appears in a token.

## Authorization Decision

```text
Token valid?
  | no -> Deny
  v
Grant active?
  | no -> Deny
  v
Requested resource in scope?
  | no -> Deny
  v
Allow
```

Expiration and revocation are different mechanisms. A revoked grant must immediately prevent further access even if a token has not yet expired.

## Kill Switch

Patients should have a visible control to revoke active access. Revocation must update persistent authorization state and be checked on every protected access.

## Doctor Portal

Doctor access should expose only records covered by the active grant. Doctors should never receive unrestricted database credentials.

## Audit

Both successful and denied access attempts should be recorded. Patients should be able to inspect meaningful access history.

## Enforcement

Access-control checks must happen on the backend and, where applicable, through database Row Level Security. The frontend is never the final enforcement boundary.
