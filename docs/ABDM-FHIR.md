# ABDM and FHIR Readiness

## Objective

MediVault should structure healthcare information using interoperable healthcare concepts rather than a proprietary representation that cannot be translated later.

The prototype should therefore be FHIR-compatible where practical and designed for eventual integration with India's ABDM ecosystem.

## FHIR-Oriented Mapping

| MediVault Concept | FHIR Concept |
|---|---|
| Patient | Patient |
| Medical condition | Condition |
| Laboratory result | Observation |
| Vital sign | Observation |
| Prescription | MedicationRequest |
| Medication | Medication / MedicationRequest |
| Procedure | Procedure |
| Medical document | DocumentReference |
| Clinical document content | Binary |
| Hospital | Organization |
| Doctor | Practitioner |

## Observation

Example conceptual representation:

```json
{
  "resourceType": "Observation",
  "status": "final",
  "code": { "text": "Blood Pressure" },
  "valueQuantity": {
    "value": 120,
    "unit": "mmHg"
  }
}
```

Production implementation should use appropriate standardized coding systems and applicable FHIR profiles rather than relying only on free text.

## MedicationRequest

Prescriptions should be represented as medication-request information where appropriate. The system must distinguish medication explicitly prescribed from medication merely mentioned or inferred by AI.

## DocumentReference

The original medical report should remain linked to structured data through document provenance.

```text
DocumentReference
      |
      +-- Original Medical Document
              |
              +-- Extracted Structured Data
```

## ABDM Readiness

The architecture should allow future ABDM integration without replacing the internal medical-record model. Potential future capabilities include ABHA-linked identity, consent-aware exchange, health information exchange, standardized records, and ABDM-compatible integrations.

## Scope Boundary

FHIR-ready does not mean ABDM-certified or officially integrated. MediVault should only claim integrations and certifications that have actually been implemented and verified.
