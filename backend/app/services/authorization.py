from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import (
    AccessLog,
    AuditOutcome,
    Doctor,
    GrantStatus,
    MedicalDocument,
    Patient,
    ShareGrant,
    User,
    UserRole,
)


class AuthorizationError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _is_grant_active(grant: ShareGrant, now: datetime | None = None) -> bool:
    current = now or datetime.now(UTC)
    if grant.status == GrantStatus.revoked or grant.revoked_at is not None:
        return False
    expires_at = grant.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= current:
        return False
    return grant.status == GrantStatus.active


def _record_type_allowed(scope: dict, record_type: str) -> bool:
    allowed = scope.get("record_types") or []
    return not allowed or record_type in allowed or record_type.endswith("s") and record_type.rstrip("s") in allowed


def _document_in_scope(scope: dict, document_id: str | None) -> bool:
    doc_ids = scope.get("document_ids") or []
    if not doc_ids:
        return True
    return document_id is not None and document_id in doc_ids


def get_active_grant(db: Session, patient_id: str, doctor_id: str) -> ShareGrant | None:
    grant = (
        db.query(ShareGrant)
        .filter(
            ShareGrant.patient_id == patient_id,
            ShareGrant.doctor_id == doctor_id,
            ShareGrant.status == GrantStatus.active,
        )
        .order_by(ShareGrant.issued_at.desc())
        .first()
    )
    if grant and _is_grant_active(grant):
        return grant
    if grant and not _is_grant_active(grant):
        grant.status = GrantStatus.expired
        db.commit()
    return None


def assert_patient_self(user: User, patient_id: str) -> Patient:
    if user.role != UserRole.patient or not user.patient or user.patient.id != patient_id:
        raise AuthorizationError("ACCESS_DENIED", "Not authorized for this patient")
    return user.patient


def authorize_patient_access(db: Session, user: User, patient_id: str) -> tuple[str, ShareGrant | None]:
    if user.role == UserRole.patient:
        assert_patient_self(user, patient_id)
        return "patient", None

    if user.role == UserRole.doctor and user.doctor:
        grant = get_active_grant(db, patient_id, user.doctor.id)
        if not grant:
            raise AuthorizationError("ACCESS_DENIED", "No active share grant")
        return "doctor", grant

    raise AuthorizationError("ACCESS_DENIED", "Not authorized")


def authorize_document(db: Session, user: User, document: MedicalDocument) -> ShareGrant | None:
    _, grant = authorize_patient_access(db, user, document.patient_id)
    if grant and not _document_in_scope(grant.scope, document.id):
        raise AuthorizationError("OUT_OF_SCOPE", "Document not in grant scope")
    return grant


def authorize_record(db: Session, user: User, patient_id: str, record_type: str, document_id: str | None = None) -> ShareGrant | None:
    _, grant = authorize_patient_access(db, user, patient_id)
    if grant:
        if not _record_type_allowed(grant.scope, record_type):
            raise AuthorizationError("OUT_OF_SCOPE", "Record type not in grant scope")
        if not _document_in_scope(grant.scope, document_id):
            raise AuthorizationError("OUT_OF_SCOPE", "Record not in grant scope")
    return grant


def write_audit(
    db: Session,
    *,
    action: str,
    outcome: AuditOutcome,
    request_id: str,
    actor: User | None = None,
    actor_role: str | None = None,
    patient_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
):
    entry = AccessLog(
        action=action,
        outcome=outcome,
        request_id=request_id,
        actor_id=actor.id if actor else None,
        actor_role=actor_role or (actor.role.value if actor else "system"),
        patient_id=patient_id,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        extra_metadata=metadata,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
