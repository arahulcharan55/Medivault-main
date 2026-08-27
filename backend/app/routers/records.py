from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_request_id
from app.models import (
    AllergyIntolerance,
    AuditOutcome,
    Condition,
    MedicalDocument,
    Medication,
    Observation,
    Patient,
    Procedure,
    User,
    UserRole,
)
from app.schemas import TimelineItem, TimelineResponse
from app.services.authorization import AuthorizationError, authorize_patient_access, authorize_record, write_audit
from app.services.fhir import build_fhir_bundle
from app.services.summary import build_health_summary

router = APIRouter(prefix="/records", tags=["records"])

RECORD_TYPE_ALIASES = {
    "observation": "observations",
    "observations": "observations",
    "medication": "medications",
    "medications": "medications",
    "condition": "conditions",
    "conditions": "conditions",
    "procedure": "procedures",
    "procedures": "procedures",
    "allergy": "allergies",
    "allergies": "allergies",
}


def _build_timeline(
    db: Session,
    patient_id: str,
    record_types: list[str] | None = None,
    query: str | None = None,
) -> list[TimelineItem]:
    allowed: set[str] | None = None
    if record_types:
        allowed = {RECORD_TYPE_ALIASES.get(t, t) for t in record_types}

    items: list[TimelineItem] = []
    if allowed is None or "observations" in allowed:
        for obs in db.query(Observation).filter(Observation.patient_id == patient_id).all():
            items.append(
                TimelineItem(
                    type="observation",
                    id=obs.id,
                    display_name=obs.display_name,
                    value=obs.value,
                    unit=obs.unit,
                    interpretation=obs.interpretation,
                    effective_time=obs.effective_time,
                    document_id=obs.document_id,
                )
            )
    if allowed is None or "medications" in allowed:
        for med in db.query(Medication).filter(Medication.patient_id == patient_id).all():
            value = " ".join(filter(None, [med.dosage, med.frequency])) or med.instructions
            items.append(
                TimelineItem(
                    type="medication",
                    id=med.id,
                    display_name=med.medication_name,
                    value=value,
                    document_id=med.document_id,
                )
            )
    if allowed is None or "conditions" in allowed:
        for cond in db.query(Condition).filter(Condition.patient_id == patient_id).all():
            items.append(
                TimelineItem(
                    type="condition",
                    id=cond.id,
                    display_name=cond.display_name,
                    effective_time=cond.onset_date,
                    document_id=cond.document_id,
                )
            )
    if allowed is None or "procedures" in allowed:
        for proc in db.query(Procedure).filter(Procedure.patient_id == patient_id).all():
            items.append(
                TimelineItem(
                    type="procedure",
                    id=proc.id,
                    display_name=proc.display_name,
                    effective_time=proc.performed_date,
                    document_id=proc.document_id,
                )
            )
    if allowed is None or "allergies" in allowed:
        for allergy in db.query(AllergyIntolerance).filter(AllergyIntolerance.patient_id == patient_id).all():
            items.append(
                TimelineItem(
                    type="allergy",
                    id=allergy.id,
                    display_name=allergy.substance,
                    value=allergy.reaction,
                    document_id=allergy.document_id,
                )
            )

    if query:
        needle = query.lower()
        items = [
            item
            for item in items
            if needle in item.display_name.lower()
            or needle in (item.value or "").lower()
            or needle in item.type.lower()
        ]

    items.sort(key=lambda x: x.effective_time or "", reverse=True)
    return items


@router.get("/timeline", response_model=TimelineResponse)
def get_timeline(
    patient_id: str | None = None,
    q: str | None = Query(default=None, description="Search display names and values"),
    record_type: list[str] | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
):
    target_patient_id = patient_id
    if user.role == UserRole.patient and user.patient:
        if patient_id and patient_id != user.patient.id:
            write_audit(db, action="ACCESS_DENIED", outcome=AuditOutcome.failure, request_id=request_id, actor=user, patient_id=patient_id, resource_type="timeline")
            raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Not authorized for this patient"})
        target_patient_id = user.patient.id
    if not target_patient_id:
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "patient_id required"})

    try:
        _, grant = authorize_patient_access(db, user, target_patient_id)
    except AuthorizationError as exc:
        write_audit(db, action="ACCESS_DENIED", outcome=AuditOutcome.failure, request_id=request_id, actor=user, patient_id=target_patient_id, resource_type="timeline")
        raise HTTPException(status_code=403, detail={"code": exc.code, "message": exc.message})

    scoped_types = record_type
    if grant:
        grant_types = grant.scope.get("record_types") or []
        if grant_types:
            scoped_types = grant_types if not record_type else [t for t in record_type if t in grant_types or RECORD_TYPE_ALIASES.get(t) in grant_types]

    items = _build_timeline(db, target_patient_id, record_types=scoped_types, query=q)
    write_audit(db, action="RECORD_VIEW", outcome=AuditOutcome.success, request_id=request_id, actor=user, patient_id=target_patient_id, resource_type="timeline")
    return TimelineResponse(items=items, total=len(items))


@router.get("/summary")
def get_summary(
    patient_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
):
    target_patient_id = patient_id or (user.patient.id if user.patient else None)
    if not target_patient_id:
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "patient_id required"})
    try:
        authorize_patient_access(db, user, target_patient_id)
    except AuthorizationError as exc:
        write_audit(db, action="ACCESS_DENIED", outcome=AuditOutcome.failure, request_id=request_id, actor=user, patient_id=target_patient_id, resource_type="summary")
        raise HTTPException(status_code=403, detail={"code": exc.code, "message": exc.message})
    summary = build_health_summary(db, target_patient_id)
    write_audit(db, action="RECORD_VIEW", outcome=AuditOutcome.success, request_id=request_id, actor=user, patient_id=target_patient_id, resource_type="summary")
    return summary


@router.get("/fhir")
def export_fhir(
    patient_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
):
    target_patient_id = patient_id or (user.patient.id if user.patient else None)
    if not target_patient_id:
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "patient_id required"})
    try:
        authorize_patient_access(db, user, target_patient_id)
    except AuthorizationError as exc:
        write_audit(db, action="ACCESS_DENIED", outcome=AuditOutcome.failure, request_id=request_id, actor=user, patient_id=target_patient_id, resource_type="fhir")
        raise HTTPException(status_code=403, detail={"code": exc.code, "message": exc.message})

    patient = db.query(Patient).filter(Patient.id == target_patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Patient not found"})

    bundle = build_fhir_bundle(
        patient,
        observations=db.query(Observation).filter(Observation.patient_id == target_patient_id).all(),
        medications=db.query(Medication).filter(Medication.patient_id == target_patient_id).all(),
        conditions=db.query(Condition).filter(Condition.patient_id == target_patient_id).all(),
        procedures=db.query(Procedure).filter(Procedure.patient_id == target_patient_id).all(),
        allergies=db.query(AllergyIntolerance).filter(AllergyIntolerance.patient_id == target_patient_id).all(),
        documents=db.query(MedicalDocument)
        .filter(MedicalDocument.patient_id == target_patient_id, MedicalDocument.deleted_at.is_(None))
        .all(),
    )
    write_audit(db, action="FHIR_EXPORT", outcome=AuditOutcome.success, request_id=request_id, actor=user, patient_id=target_patient_id, resource_type="fhir")
    return bundle


@router.get("/observations")
def list_observations(patient_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db), request_id: str = Depends(get_request_id)):
    target_patient_id = patient_id or (user.patient.id if user.patient else None)
    if not target_patient_id:
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "patient_id required"})
    try:
        authorize_record(db, user, target_patient_id, "observations")
    except AuthorizationError as exc:
        write_audit(db, action="ACCESS_DENIED", outcome=AuditOutcome.failure, request_id=request_id, actor=user, patient_id=target_patient_id, resource_type="observations")
        raise HTTPException(status_code=403, detail={"code": exc.code, "message": exc.message})
    rows = db.query(Observation).filter(Observation.patient_id == target_patient_id).all()
    write_audit(db, action="RECORD_VIEW", outcome=AuditOutcome.success, request_id=request_id, actor=user, patient_id=target_patient_id, resource_type="observations")
    return rows
