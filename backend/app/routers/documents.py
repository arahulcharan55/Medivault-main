from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, get_db
from app.dependencies import get_current_user, get_request_id
from app.models import AuditOutcome, ExtractionJob, MedicalDocument, ProcessingStatus, Provenance, User, UserRole
from app.schemas import DocumentResponse, ExtractionJobResponse, ExtractionReviewRequest
from app.services.authorization import AuthorizationError, authorize_document, write_audit
from app.services.processing import persist_extracted_records, process_document
from app.services.storage import build_object_key, compute_hash, save_document, validate_upload

router = APIRouter(prefix="/documents", tags=["documents"])


def _run_processing(document_id: str):
    db = SessionLocal()
    try:
        document = db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
        if document:
            process_document(db, document)
    finally:
        db.close()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
):
    if user.role != UserRole.patient or not user.patient:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Patients only"})

    content = await file.read()
    mime_type = file.content_type or "application/octet-stream"
    try:
        validate_upload(mime_type, len(content))
    except ValueError as exc:
        raise HTTPException(status_code=415, detail={"code": "INVALID_FILE_TYPE", "message": str(exc)})

    source_hash = compute_hash(content)
    duplicate = (
        db.query(MedicalDocument)
        .filter(
            MedicalDocument.patient_id == user.patient.id,
            MedicalDocument.source_hash == source_hash,
            MedicalDocument.deleted_at.is_(None),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail={"code": "DUPLICATE_DOCUMENT", "message": "This file was already uploaded", "document_id": duplicate.id},
        )

    document = MedicalDocument(
        patient_id=user.patient.id,
        filename=file.filename or "upload",
        mime_type=mime_type,
        file_size=len(content),
        source_hash=source_hash,
        storage_path="pending",
        processing_status=ProcessingStatus.pending,
    )
    db.add(document)
    db.flush()
    document.storage_path = build_object_key(user.patient.id, document.id, source_hash, mime_type)
    await save_document(content, document.storage_path)
    db.commit()
    db.refresh(document)

    write_audit(
        db,
        action="DOCUMENT_UPLOAD",
        outcome=AuditOutcome.success,
        request_id=request_id,
        actor=user,
        patient_id=user.patient.id,
        resource_type="document",
        resource_id=document.id,
        ip_address=request.client.host if request.client else None,
    )

    background_tasks.add_task(_run_processing, document.id)
    write_audit(
        db,
        action="EXTRACTION_STARTED",
        outcome=AuditOutcome.success,
        request_id=request_id,
        actor=user,
        patient_id=user.patient.id,
        resource_type="document",
        resource_id=document.id,
    )
    return DocumentResponse.model_validate(document)


@router.get("", response_model=list[DocumentResponse])
def list_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == UserRole.patient and user.patient:
        docs = db.query(MedicalDocument).filter(MedicalDocument.patient_id == user.patient.id, MedicalDocument.deleted_at.is_(None)).order_by(MedicalDocument.uploaded_at.desc()).all()
        return [DocumentResponse.model_validate(d) for d in docs]
    raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Use patient account or doctor records endpoint"})


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db), request_id: str = Depends(get_request_id)):
    document = db.query(MedicalDocument).filter(MedicalDocument.id == document_id, MedicalDocument.deleted_at.is_(None)).first()
    if not document:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Document not found"})
    try:
        authorize_document(db, user, document)
    except AuthorizationError as exc:
        write_audit(db, action="ACCESS_DENIED", outcome=AuditOutcome.failure, request_id=request_id, actor=user, patient_id=document.patient_id, resource_type="document", resource_id=document.id)
        raise HTTPException(status_code=403, detail={"code": exc.code, "message": exc.message})
    write_audit(db, action="DOCUMENT_VIEW", outcome=AuditOutcome.success, request_id=request_id, actor=user, patient_id=document.patient_id, resource_type="document", resource_id=document.id)
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/download")
def download_document(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db), request_id: str = Depends(get_request_id)):
    document = db.query(MedicalDocument).filter(MedicalDocument.id == document_id, MedicalDocument.deleted_at.is_(None)).first()
    if not document:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Document not found"})
    try:
        authorize_document(db, user, document)
    except AuthorizationError as exc:
        write_audit(db, action="ACCESS_DENIED", outcome=AuditOutcome.failure, request_id=request_id, actor=user, patient_id=document.patient_id, resource_type="document", resource_id=document.id)
        raise HTTPException(status_code=403, detail={"code": exc.code, "message": exc.message})

    file_path = settings.storage_path + "/" + document.storage_path
    write_audit(db, action="DOCUMENT_DOWNLOAD", outcome=AuditOutcome.success, request_id=request_id, actor=user, patient_id=document.patient_id, resource_type="document", resource_id=document.id)
    return FileResponse(file_path, filename=document.filename, media_type=document.mime_type)


@router.delete("/{document_id}")
def delete_document(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db), request_id: str = Depends(get_request_id)):
    if user.role != UserRole.patient or not user.patient:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Patients only"})
    document = db.query(MedicalDocument).filter(MedicalDocument.id == document_id, MedicalDocument.patient_id == user.patient.id, MedicalDocument.deleted_at.is_(None)).first()
    if not document:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Document not found"})
    document.deleted_at = datetime.now(UTC)
    db.commit()
    write_audit(db, action="DOCUMENT_DELETE", outcome=AuditOutcome.success, request_id=request_id, actor=user, patient_id=user.patient.id, resource_type="document", resource_id=document.id)
    return {"status": "deleted"}


@router.get("/{document_id}/extraction", response_model=ExtractionJobResponse)
def get_latest_extraction(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db), request_id: str = Depends(get_request_id)):
    document = db.query(MedicalDocument).filter(MedicalDocument.id == document_id, MedicalDocument.deleted_at.is_(None)).first()
    if not document:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Document not found"})
    try:
        authorize_document(db, user, document)
    except AuthorizationError as exc:
        write_audit(db, action="ACCESS_DENIED", outcome=AuditOutcome.failure, request_id=request_id, actor=user, patient_id=document.patient_id, resource_type="extraction", resource_id=document.id)
        raise HTTPException(status_code=403, detail={"code": exc.code, "message": exc.message})
    job = (
        db.query(ExtractionJob)
        .filter(ExtractionJob.document_id == document_id)
        .order_by(ExtractionJob.started_at.desc())
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "No extraction job yet"})
    return ExtractionJobResponse.model_validate(job)


@router.post("/{document_id}/review", response_model=ExtractionJobResponse)
def review_extraction(
    document_id: str,
    payload: ExtractionReviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
):
    if user.role != UserRole.patient or not user.patient:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Patients only"})
    document = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.patient_id == user.patient.id,
        MedicalDocument.deleted_at.is_(None),
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Document not found"})
    job = (
        db.query(ExtractionJob)
        .filter(ExtractionJob.document_id == document_id)
        .order_by(ExtractionJob.started_at.desc())
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "No extraction job yet"})

    if payload.action == "reject":
        job.status = ProcessingStatus.failed
        job.error_code = "REJECTED_BY_PATIENT"
        job.error_message = "Patient rejected extracted facts"
        document.processing_status = ProcessingStatus.failed
    else:
        provenance = db.query(Provenance).filter(Provenance.extraction_job_id == job.id).first()
        if not provenance:
            provenance = Provenance(
                extraction_job_id=job.id,
                document_id=document.id,
                model=job.model,
                provider=job.llm_provider,
                confidence=0.5,
            )
            db.add(provenance)
            db.flush()
        if job.extracted_json:
            persist_extracted_records(db, document, job.extracted_json, provenance)
        job.status = ProcessingStatus.validated
        document.processing_status = ProcessingStatus.validated

    db.commit()
    db.refresh(job)
    write_audit(
        db,
        action="EXTRACTION_REVIEWED",
        outcome=AuditOutcome.success,
        request_id=request_id,
        actor=user,
        patient_id=user.patient.id,
        resource_type="document",
        resource_id=document.id,
        metadata={"action": payload.action},
    )
    return ExtractionJobResponse.model_validate(job)


@router.post("/{document_id}/process", response_model=ExtractionJobResponse)
def trigger_processing(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != UserRole.patient or not user.patient:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Patients only"})
    document = db.query(MedicalDocument).filter(MedicalDocument.id == document_id, MedicalDocument.patient_id == user.patient.id).first()
    if not document:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Document not found"})
    job = process_document(db, document)
    return ExtractionJobResponse.model_validate(job)
