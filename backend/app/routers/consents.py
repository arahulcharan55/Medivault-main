from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user, get_request_id
from app.models import AuditOutcome, Doctor, GrantStatus, ShareGrant, User, UserRole
from app.schemas import ConsentCreateRequest, ConsentResponse
from app.services.authorization import AuthorizationError, assert_patient_self, write_audit
from app.services.storage import generate_token_identifier

router = APIRouter(prefix="/consents", tags=["consents"])


def _to_response(grant: ShareGrant) -> ConsentResponse:
    return ConsentResponse(
        id=grant.id,
        patient_id=grant.patient_id,
        doctor_id=grant.doctor_id,
        doctor_name=grant.doctor.name if grant.doctor else None,
        scope=grant.scope,
        permissions=grant.permissions,
        issued_at=grant.issued_at,
        expires_at=grant.expires_at,
        revoked_at=grant.revoked_at,
        status=grant.status.value,
        token_identifier=grant.token_identifier,
    )


@router.post("", response_model=ConsentResponse)
def create_consent(
    payload: ConsentCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
):
    if user.role != UserRole.patient or not user.patient:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Patients only"})

    doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Doctor not found"})

    expires_at = payload.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "expires_at must be in the future"})

    grant = ShareGrant(
        patient_id=user.patient.id,
        doctor_id=payload.doctor_id,
        scope=payload.scope,
        permissions=payload.permissions,
        expires_at=expires_at,
        status=GrantStatus.active,
        token_identifier=generate_token_identifier(),
    )
    db.add(grant)
    db.commit()
    db.refresh(grant)

    write_audit(
        db,
        action="SHARE_CREATED",
        outcome=AuditOutcome.success,
        request_id=request_id,
        actor=user,
        patient_id=user.patient.id,
        resource_type="consent",
        resource_id=grant.id,
    )
    grant = db.query(ShareGrant).options(joinedload(ShareGrant.doctor)).filter(ShareGrant.id == grant.id).first()
    return _to_response(grant)


@router.get("", response_model=list[ConsentResponse])
def list_consents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == UserRole.patient and user.patient:
        grants = db.query(ShareGrant).options(joinedload(ShareGrant.doctor)).filter(ShareGrant.patient_id == user.patient.id).all()
        return [_to_response(g) for g in grants]
    if user.role == UserRole.doctor and user.doctor:
        grants = db.query(ShareGrant).options(joinedload(ShareGrant.doctor)).filter(ShareGrant.doctor_id == user.doctor.id).all()
        return [_to_response(g) for g in grants]
    raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Not authorized"})


@router.patch("/{grant_id}/revoke", response_model=ConsentResponse)
def revoke_consent(grant_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db), request_id: str = Depends(get_request_id)):
    if user.role != UserRole.patient or not user.patient:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Patients only"})

    grant = db.query(ShareGrant).options(joinedload(ShareGrant.doctor)).filter(ShareGrant.id == grant_id, ShareGrant.patient_id == user.patient.id).first()
    if not grant:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Grant not found"})

    grant.revoked_at = datetime.now(UTC)
    grant.status = GrantStatus.revoked
    db.commit()
    db.refresh(grant)

    write_audit(
        db,
        action="SHARE_REVOKED",
        outcome=AuditOutcome.success,
        request_id=request_id,
        actor=user,
        patient_id=user.patient.id,
        resource_type="consent",
        resource_id=grant.id,
    )
    return _to_response(grant)
