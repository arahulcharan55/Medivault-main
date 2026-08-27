"""Minimal FHIR R4 collection bundle export from MediVault records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.models import AllergyIntolerance, Condition, MedicalDocument, Medication, Observation, Patient, Procedure


def _qty(value: str | None, unit: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    numeric = None
    try:
        numeric = float(str(value).replace("/", "").split()[0]) if "/" not in str(value) else None
    except ValueError:
        numeric = None
    if numeric is not None and unit:
        return {"valueQuantity": {"value": numeric, "unit": unit}}
    if value:
        return {"valueString": f"{value}{(' ' + unit) if unit else ''}"}
    return None


def build_fhir_bundle(
    patient: Patient,
    *,
    observations: list[Observation],
    medications: list[Medication],
    conditions: list[Condition],
    procedures: list[Procedure],
    allergies: list[AllergyIntolerance],
    documents: list[MedicalDocument],
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    patient_ref = f"Patient/{patient.id}"

    entries.append(
        {
            "fullUrl": f"urn:uuid:{patient.id}",
            "resource": {
                "resourceType": "Patient",
                "id": patient.id,
                "name": [{"text": patient.name}],
                "birthDate": patient.date_of_birth or None,
            },
        }
    )

    for obs in observations:
        resource: dict[str, Any] = {
            "resourceType": "Observation",
            "id": obs.id,
            "status": "final",
            "code": {"text": obs.display_name, "coding": [{"system": "http://loinc.org", "code": obs.code}] if obs.code else []},
            "subject": {"reference": patient_ref},
            "effectiveDateTime": obs.effective_time,
        }
        qty = _qty(obs.value, obs.unit)
        if qty:
            resource.update(qty)
        if obs.reference_range:
            resource["referenceRange"] = [{"text": obs.reference_range}]
        entries.append({"fullUrl": f"urn:uuid:{obs.id}", "resource": resource})

    for med in medications:
        entries.append(
            {
                "fullUrl": f"urn:uuid:{med.id}",
                "resource": {
                    "resourceType": "MedicationStatement",
                    "id": med.id,
                    "status": "active",
                    "medicationCodeableConcept": {"text": med.medication_name},
                    "subject": {"reference": patient_ref},
                    "dosage": [
                        {
                            "text": med.instructions or " ".join(filter(None, [med.dosage, med.frequency])),
                            "doseAndRate": [{"doseQuantity": {"unit": med.dosage}}] if med.dosage else [],
                        }
                    ],
                },
            }
        )

    for cond in conditions:
        entries.append(
            {
                "fullUrl": f"urn:uuid:{cond.id}",
                "resource": {
                    "resourceType": "Condition",
                    "id": cond.id,
                    "clinicalStatus": {"coding": [{"code": cond.clinical_status or "active"}]},
                    "code": {"text": cond.display_name},
                    "subject": {"reference": patient_ref},
                    "onsetDateTime": cond.onset_date,
                },
            }
        )

    for proc in procedures:
        entries.append(
            {
                "fullUrl": f"urn:uuid:{proc.id}",
                "resource": {
                    "resourceType": "Procedure",
                    "id": proc.id,
                    "status": "completed",
                    "code": {"text": proc.display_name},
                    "subject": {"reference": patient_ref},
                    "performedDateTime": proc.performed_date,
                    "performer": [{"actor": {"display": proc.performer}}] if proc.performer else [],
                },
            }
        )

    for allergy in allergies:
        entries.append(
            {
                "fullUrl": f"urn:uuid:{allergy.id}",
                "resource": {
                    "resourceType": "AllergyIntolerance",
                    "id": allergy.id,
                    "clinicalStatus": {"coding": [{"code": "active"}]},
                    "code": {"text": allergy.substance},
                    "patient": {"reference": patient_ref},
                    "note": [{"text": allergy.reaction}] if allergy.reaction else [],
                },
            }
        )

    for doc in documents:
        entries.append(
            {
                "fullUrl": f"urn:uuid:{doc.id}",
                "resource": {
                    "resourceType": "DocumentReference",
                    "id": doc.id,
                    "status": "current",
                    "type": {"text": "Medical document"},
                    "subject": {"reference": patient_ref},
                    "date": doc.document_date or (doc.uploaded_at.isoformat() if doc.uploaded_at else None),
                    "content": [
                        {
                            "attachment": {
                                "contentType": doc.mime_type,
                                "title": doc.filename,
                                "size": doc.file_size,
                            }
                        }
                    ],
                },
            }
        )

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": datetime.now(UTC).isoformat(),
        "total": len(entries),
        "meta": {"tag": [{"system": "https://medivault.local", "code": "prototype-fhir-export"}]},
        "entry": entries,
    }
