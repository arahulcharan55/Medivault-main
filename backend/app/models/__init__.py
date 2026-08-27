import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    patient = "patient"
    doctor = "doctor"
    admin = "admin"


class ProcessingStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    validated = "validated"
    human_review = "human_review"
    failed = "failed"


class GrantStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    revoked = "revoked"


class AuditOutcome(str, enum.Enum):
    success = "success"
    failure = "failure"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patient: Mapped["Patient | None"] = relationship(back_populates="user", uselist=False)
    doctor: Mapped["Doctor | None"] = relationship(back_populates="user", uselist=False)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    date_of_birth: Mapped[str | None] = mapped_column(String(32), nullable=True)
    contact_information: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="patient")
    documents: Mapped[list["MedicalDocument"]] = relationship(back_populates="patient")
    observations: Mapped[list["Observation"]] = relationship(back_populates="patient")
    medications: Mapped[list["Medication"]] = relationship(back_populates="patient")
    conditions: Mapped[list["Condition"]] = relationship(back_populates="patient")
    procedures: Mapped[list["Procedure"]] = relationship(back_populates="patient")
    allergies: Mapped[list["AllergyIntolerance"]] = relationship(back_populates="patient")
    share_grants: Mapped[list["ShareGrant"]] = relationship(back_populates="patient", foreign_keys="ShareGrant.patient_id")


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    specialization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    license_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="doctor")
    share_grants: Mapped[list["ShareGrant"]] = relationship(back_populates="doctor", foreign_keys="ShareGrant.doctor_id")


class MedicalDocument(Base):
    __tablename__ = "medical_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    storage_path: Mapped[str] = mapped_column(String(512))
    filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(128))
    file_size: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processing_status: Mapped[ProcessingStatus] = mapped_column(Enum(ProcessingStatus), default=ProcessingStatus.pending)
    document_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_hash: Mapped[str] = mapped_column(String(64), index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patient: Mapped[Patient] = relationship(back_populates="documents")
    extraction_jobs: Mapped[list["ExtractionJob"]] = relationship(back_populates="document")


class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("medical_documents.id"), index=True)
    status: Mapped[ProcessingStatus] = mapped_column(Enum(ProcessingStatus), default=ProcessingStatus.processing)
    ocr_provider: Mapped[str] = mapped_column(String(64))
    llm_provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    raw_ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[MedicalDocument] = relationship(back_populates="extraction_jobs")


class Provenance(Base):
    __tablename__ = "provenance"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    extraction_job_id: Mapped[str] = mapped_column(String(36), ForeignKey("extraction_jobs.id"), index=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("medical_documents.id"), index=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ocr_segment: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(128))
    provider: Mapped[str] = mapped_column(String(64))
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("medical_documents.id"), nullable=True)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_name: Mapped[str] = mapped_column(String(255))
    value: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    effective_time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reference_range: Mapped[str | None] = mapped_column(String(128), nullable=True)
    interpretation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    provenance_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("provenance.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[Patient] = relationship(back_populates="observations")


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("medical_documents.id"), nullable=True)
    medication_name: Mapped[str] = mapped_column(String(255))
    dosage: Mapped[str | None] = mapped_column(String(128), nullable=True)
    route: Mapped[str | None] = mapped_column(String(64), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(128), nullable=True)
    duration: Mapped[str | None] = mapped_column(String(128), nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("provenance.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[Patient] = relationship(back_populates="medications")


class Condition(Base):
    __tablename__ = "conditions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("medical_documents.id"), nullable=True)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_name: Mapped[str] = mapped_column(String(255))
    clinical_status: Mapped[str] = mapped_column(String(32), default="active")
    onset_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    provenance_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("provenance.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[Patient] = relationship(back_populates="conditions")


class Procedure(Base):
    __tablename__ = "procedures"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("medical_documents.id"), nullable=True)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_name: Mapped[str] = mapped_column(String(255))
    performed_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    performer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provenance_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("provenance.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[Patient] = relationship(back_populates="procedures")


class AllergyIntolerance(Base):
    __tablename__ = "allergy_intolerances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("medical_documents.id"), nullable=True)
    substance: Mapped[str] = mapped_column(String(255))
    reaction: Mapped[str | None] = mapped_column(String(255), nullable=True)
    clinical_status: Mapped[str] = mapped_column(String(32), default="active")
    provenance_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("provenance.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[Patient] = relationship(back_populates="allergies")


class ShareGrant(Base):
    __tablename__ = "share_grants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("doctors.id"), index=True)
    scope: Mapped[dict] = mapped_column(JSON)
    permissions: Mapped[list] = mapped_column(JSON, default=list)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[GrantStatus] = mapped_column(Enum(GrantStatus), default=GrantStatus.active)
    token_identifier: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patient: Mapped[Patient] = relationship(back_populates="share_grants", foreign_keys=[patient_id])
    doctor: Mapped[Doctor] = relationship(back_populates="share_grants", foreign_keys=[doctor_id])


class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("patients.id"), nullable=True, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    actor_role: Mapped[str] = mapped_column(String(32))
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    outcome: Mapped[AuditOutcome] = mapped_column(Enum(AuditOutcome))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    extra_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
