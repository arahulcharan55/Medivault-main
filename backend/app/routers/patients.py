from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_request_id
from app.models import AuditOutcome, User, UserRole
from app.schemas import PatientUpdateRequest, UserProfileResponse
from app.services.auth import get_user_profile
from app.services.authorization import assert_patient_self, write_audit

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Patients only"})
    return get_user_profile(db, user)


@router.patch("/me", response_model=UserProfileResponse)
def update_my_profile(
    payload: PatientUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
):
    if not user.patient:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Patients only"})
    patient = assert_patient_self(user, user.patient.id)
    if payload.name is not None:
        patient.name = payload.name
    if payload.date_of_birth is not None:
        patient.date_of_birth = payload.date_of_birth
    if payload.contact_information is not None:
        patient.contact_information = payload.contact_information
    db.commit()
    write_audit(
        db,
        action="PROFILE_UPDATED",
        outcome=AuditOutcome.success,
        request_id=request_id,
        actor=user,
        patient_id=patient.id,
        resource_type="patient",
        resource_id=patient.id,
    )
    return get_user_profile(db, user)
