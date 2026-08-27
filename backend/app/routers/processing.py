from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import ExtractionJob, MedicalDocument, User, UserRole
from app.schemas import ExtractionJobResponse
from app.services.authorization import AuthorizationError, authorize_document

router = APIRouter(prefix="/processing", tags=["processing"])


@router.get("/jobs/{job_id}", response_model=ExtractionJobResponse)
def get_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Job not found"})
    document = db.query(MedicalDocument).filter(MedicalDocument.id == job.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Document not found"})
    try:
        authorize_document(db, user, document)
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail={"code": exc.code, "message": exc.message})
    return ExtractionJobResponse.model_validate(job)


@router.get("/documents/{document_id}/jobs", response_model=list[ExtractionJobResponse])
def list_document_jobs(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Document not found"})
    try:
        authorize_document(db, user, document)
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail={"code": exc.code, "message": exc.message})
    jobs = db.query(ExtractionJob).filter(ExtractionJob.document_id == document_id).order_by(ExtractionJob.started_at.desc()).all()
    return [ExtractionJobResponse.model_validate(j) for j in jobs]
