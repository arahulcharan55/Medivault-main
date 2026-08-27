"""Seed demo patient and doctor accounts for local development."""

from app.database import SessionLocal, Base, engine, ensure_sqlite_columns
from app.models import User
from app.services.auth import register_user
from app.models import UserRole

DEMO = [
    ("patient@demo.medivault", "password123", UserRole.patient, "Demo Patient"),
    ("doctor@demo.medivault", "password123", UserRole.doctor, "Dr. Demo", {"specialization": "General Medicine"}),
]


def main():
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_columns()
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Database already seeded")
            return
        for item in DEMO:
            email, password, role, name = item[:4]
            extras = item[4] if len(item) > 4 else {}
            register_user(db, email=email, password=password, role=role, name=name, **extras)
            print(f"Created {role.value}: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
