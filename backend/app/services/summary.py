from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import AllergyIntolerance, Condition, MedicalDocument, Medication, Observation, Procedure


def build_health_summary(db: Session, patient_id: str) -> dict[str, Any]:
    documents = (
        db.query(MedicalDocument)
        .filter(MedicalDocument.patient_id == patient_id, MedicalDocument.deleted_at.is_(None))
        .all()
    )
    observations = db.query(Observation).filter(Observation.patient_id == patient_id).all()
    medications = db.query(Medication).filter(Medication.patient_id == patient_id).all()
    conditions = db.query(Condition).filter(Condition.patient_id == patient_id).all()
    procedures = db.query(Procedure).filter(Procedure.patient_id == patient_id).all()
    allergies = db.query(AllergyIntolerance).filter(AllergyIntolerance.patient_id == patient_id).all()

    latest_by_name: dict[str, Observation] = {}
    for obs in observations:
        current = latest_by_name.get(obs.display_name)
        if current is None or (obs.effective_time or "") >= (current.effective_time or ""):
            latest_by_name[obs.display_name] = obs

    abnormal = [
        {
            "id": obs.id,
            "display_name": obs.display_name,
            "value": obs.value,
            "unit": obs.unit,
            "interpretation": obs.interpretation,
            "effective_time": obs.effective_time,
        }
        for obs in observations
        if obs.interpretation in {"high", "low"}
    ]

    return {
        "counts": {
            "documents": len(documents),
            "observations": len(observations),
            "medications": len(medications),
            "conditions": len(conditions),
            "procedures": len(procedures),
            "allergies": len(allergies),
        },
        "latest_observations": [
            {
                "id": obs.id,
                "display_name": obs.display_name,
                "value": obs.value,
                "unit": obs.unit,
                "interpretation": obs.interpretation,
                "effective_time": obs.effective_time,
            }
            for obs in latest_by_name.values()
        ],
        "medications": [
            {
                "id": m.id,
                "medication_name": m.medication_name,
                "dosage": m.dosage,
                "frequency": m.frequency,
            }
            for m in medications
        ],
        "conditions": [{"id": c.id, "display_name": c.display_name, "onset_date": c.onset_date} for c in conditions],
        "allergies": [{"id": a.id, "substance": a.substance, "reaction": a.reaction} for a in allergies],
        "abnormal_observations": abnormal,
        "processing": {
            "pending": sum(1 for d in documents if d.processing_status.value in {"pending", "processing", "human_review"}),
            "failed": sum(1 for d in documents if d.processing_status.value == "failed"),
            "validated": sum(1 for d in documents if d.processing_status.value == "validated"),
        },
    }
