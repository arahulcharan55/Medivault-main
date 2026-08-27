from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Doctor, User, UserRole

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("")
def list_doctors(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Patients only"})
    doctors = db.query(Doctor).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "specialization": d.specialization,
            "organization": d.organization,
        }
        for d in doctors
    ]
