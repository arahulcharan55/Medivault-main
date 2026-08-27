from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_request_id
from app.models import AuditOutcome, User, UserRole
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserProfileResponse
from app.services.auth import authenticate_user, create_access_token, get_user_profile, register_user
from app.services.authorization import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserProfileResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db), request_id: str = Depends(get_request_id)):
    try:
        user = register_user(
            db,
            email=payload.email,
            password=payload.password,
            role=UserRole(payload.role),
            name=payload.name,
            date_of_birth=payload.date_of_birth,
            specialization=payload.specialization,
            license_number=payload.license_number,
            organization=payload.organization,
        )
    except ValueError as exc:
        code = "DUPLICATE_EMAIL" if "Email" in str(exc) else "VALIDATION_ERROR"
        raise HTTPException(status_code=409 if code == "DUPLICATE_EMAIL" else 400, detail={"code": code, "message": str(exc)})

    write_audit(db, action="REGISTER_SUCCESS", outcome=AuditOutcome.success, request_id=request_id, actor=user)
    return get_user_profile(db, user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db), request_id: str = Depends(get_request_id)):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        write_audit(
            db,
            action="LOGIN_FAILURE",
            outcome=AuditOutcome.failure,
            request_id=request_id,
            actor_role="unknown",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Invalid credentials"})

    token = create_access_token(user.id, user.role)
    write_audit(
        db,
        action="LOGIN_SUCCESS",
        outcome=AuditOutcome.success,
        request_id=request_id,
        actor=user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserProfileResponse)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_profile(db, user)
