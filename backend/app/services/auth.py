import bcrypt
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Doctor, Patient, User, UserRole


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(subject: str, role: UserRole, expires_minutes: int | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes or settings.access_token_expire_minutes)
    payload = {"sub": subject, "role": role.value, "exp": expire, "iat": datetime.now(UTC)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


def register_user(db: Session, email: str, password: str, role: UserRole, name: str, **profile: Any) -> User:
    if db.query(User).filter(User.email == email).first():
        raise ValueError("Email already registered")

    user = User(email=email.lower(), password_hash=hash_password(password), role=role)
    db.add(user)
    db.flush()

    if role == UserRole.patient:
        db.add(Patient(user_id=user.id, name=name, date_of_birth=profile.get("date_of_birth")))
    elif role == UserRole.doctor:
        db.add(
            Doctor(
                user_id=user.id,
                name=name,
                specialization=profile.get("specialization"),
                license_number=profile.get("license_number"),
                organization=profile.get("organization"),
            )
        )
    else:
        raise ValueError("Unsupported role")

    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def get_user_profile(db: Session, user: User) -> dict[str, Any]:
    profile: dict[str, Any] = {"user_id": user.id, "email": user.email, "role": user.role.value}
    if user.role == UserRole.patient and user.patient:
        profile.update(
            {
                "patient_id": user.patient.id,
                "name": user.patient.name,
                "date_of_birth": user.patient.date_of_birth,
            }
        )
    if user.role == UserRole.doctor and user.doctor:
        profile.update(
            {
                "doctor_id": user.doctor.id,
                "name": user.doctor.name,
                "specialization": user.doctor.specialization,
            }
        )
    return profile
