from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: Literal["patient", "doctor"]
    name: str
    date_of_birth: str | None = None
    specialization: str | None = None
    license_number: str | None = None
    organization: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfileResponse(BaseModel):
    user_id: str
    email: EmailStr
    role: str
    patient_id: str | None = None
    doctor_id: str | None = None
    name: str | None = None
    date_of_birth: str | None = None
    specialization: str | None = None


class PatientUpdateRequest(BaseModel):
    name: str | None = None
    date_of_birth: str | None = None
    contact_information: dict | None = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    mime_type: str
    file_size: int
    processing_status: str
    document_date: str | None
    uploaded_at: datetime


class ExtractionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    status: str
    extracted_json: dict | None = None
    raw_ocr_text: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None


class ExtractionReviewRequest(BaseModel):
    action: Literal["confirm", "reject"]


class TimelineItem(BaseModel):
    type: str
    id: str
    display_name: str
    value: str | None = None
    unit: str | None = None
    interpretation: str | None = None
    effective_time: str | None = None
    document_id: str | None = None


class TimelineResponse(BaseModel):
    items: list[TimelineItem]
    total: int


class ConsentCreateRequest(BaseModel):
    doctor_id: str
    scope: dict
    permissions: list[str] = ["read"]
    expires_at: datetime


class ConsentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    doctor_id: str
    doctor_name: str | None = None
    scope: dict
    permissions: list[str]
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    status: str
    token_identifier: str


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action: str
    outcome: str
    timestamp: datetime
    actor_role: str
    resource_type: str | None
    resource_id: str | None
    request_id: str
