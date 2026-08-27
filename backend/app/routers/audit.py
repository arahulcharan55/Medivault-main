from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import AccessLog, Doctor, User, UserRole
from app.schemas import AuditLogResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=list[AuditLogResponse])
def list_audit_logs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == UserRole.patient and user.patient:
        logs = (
            db.query(AccessLog)
            .filter(AccessLog.patient_id == user.patient.id)
            .order_by(AccessLog.timestamp.desc())
            .limit(200)
            .all()
        )
        return [AuditLogResponse.model_validate(log) for log in logs]
    raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Patients only"})


@router.get("/doctors")
def list_doctors(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Patients only"})
    doctors = db.query(Doctor).all()
    return [{"id": d.id, "name": d.name, "specialization": d.specialization, "organization": d.organization} for d in doctors]


@router.get("/export", response_model=list[AuditLogResponse])
def export_audit_logs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != UserRole.patient or not user.patient:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Patients only"})
    logs = (
        db.query(AccessLog)
        .filter(AccessLog.patient_id == user.patient.id)
        .order_by(AccessLog.timestamp.desc())
        .limit(500)
        .all()
    )
    return [AuditLogResponse.model_validate(log) for log in logs]
