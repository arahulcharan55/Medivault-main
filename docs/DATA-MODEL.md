# MediVault Data Model

## Design Goals

The data model supports patient ownership, medical documents, structured observations, medications, stated diagnoses, consent, doctor access, auditability, provenance, and FHIR interoperability.

## Core Entities

```text
User
 |
 +- Patient
      |
      +- MedicalDocument -> ExtractionJob -> ExtractedRecord
      +- Observation
      +- Medication
      +- Condition
      +- Procedure
      +- Consent -> Doctor
      +- AccessLog
```

## User

```text
id
email
role
created_at
updated_at
```

Roles should be constrained rather than accepted as arbitrary client-provided strings.

## Patient

```text
id
user_id
name
date_of_birth
contact_information
created_at
updated_at
```

Sensitive fields should be minimized.

## MedicalDocument

```text
id
patient_id
storage_path
filename
mime_type
file_size
uploaded_at
processing_status
document_date
source_hash
```

`source_hash` can help detect duplicate uploads and establish document integrity.

## ExtractionJob

```text
id
document_id
status
ocr_provider
llm_provider
model
started_at
completed_at
error_code
```

## Observation

Observations represent measured or explicitly documented health data such as blood pressure, heart rate, temperature, glucose, or laboratory measurements.

```text
id
patient_id
document_id
code
display_name
value
unit
effective_time
reference_range
provenance
```

## Medication

```text
id
patient_id
document_id
medication_name
dosage
route
frequency
duration
instructions
provenance
```

## Condition

A condition represents a diagnosis or condition explicitly stated in the source document. It must not be populated solely from an AI-generated inference.

## Consent

```text
id
patient_id
doctor_id
scope
issued_at
expires_at
revoked_at
status
token_identifier
```

The scope should specify exactly what the doctor may access.

## AccessLog

```text
id
patient_id
actor_id
actor_role
resource_id
action
outcome
timestamp
ip_address
user_agent
request_id
```

## Provenance

Structured data should retain a relationship to its source document and extraction process:

```text
Structured Fact -> Medical Document -> Page/OCR Segment -> Extraction Job
```

This enables evidence-backed reconstruction of the medical timeline.

## Data Retention

Retention and deletion rules must be explicitly defined before production deployment. Deletion workflows should account for original documents, extracted records, audit records, sharing records, backups, and derived data.
