from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from fpdf import FPDF

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import UserRole
from app.services.auth import register_user
from app.services.extractor import mock_structured_extraction


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    register_user(db, "a@demo.medivault", "password123", UserRole.patient, "Patient A")
    register_user(db, "b@demo.medivault", "password123", UserRole.patient, "Patient B")
    register_user(db, "doctor@demo.medivault", "password123", UserRole.doctor, "Dr X", specialization="Medicine")
    db.close()


client = TestClient(app)


def _login(email: str) -> str:
    r = client.post("/v1/auth/login", json={"email": email, "password": "password123"})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_patient_cannot_access_other_patient_timeline():
    token_a = _login("a@demo.medivault")
    patient_b = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {_login('b@demo.medivault')}"}).json()
    r = client.get(f"/v1/records/timeline?patient_id={patient_b['patient_id']}", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "ACCESS_DENIED"


def test_doctor_denied_without_consent():
    token_doc = _login("doctor@demo.medivault")
    patient_a = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {_login('a@demo.medivault')}"}).json()
    r = client.get(f"/v1/doctor/patients/{patient_a['patient_id']}/timeline", headers={"Authorization": f"Bearer {token_doc}"})
    assert r.status_code == 403


def test_doctor_access_with_consent():
    token_a = _login("a@demo.medivault")
    token_doc = _login("doctor@demo.medivault")
    me_a = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"}).json()
    me_doc = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token_doc}"}).json()
    exp = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    c = client.post(
        "/v1/consents",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "doctor_id": me_doc["doctor_id"],
            "scope": {"record_types": ["observations", "medications", "conditions", "procedures", "allergies"]},
            "permissions": ["read"],
            "expires_at": exp,
        },
    )
    assert c.status_code == 200
    r = client.get(f"/v1/doctor/patients/{me_a['patient_id']}/timeline", headers={"Authorization": f"Bearer {token_doc}"})
    assert r.status_code == 200


def test_revoked_consent_denied():
    token_b = _login("b@demo.medivault")
    token_doc = _login("doctor@demo.medivault")
    me_b = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"}).json()
    me_doc = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token_doc}"}).json()
    exp = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    grant = client.post(
        "/v1/consents",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"doctor_id": me_doc["doctor_id"], "scope": {"record_types": ["observations"]}, "permissions": ["read"], "expires_at": exp},
    ).json()
    client.patch(f"/v1/consents/{grant['id']}/revoke", headers={"Authorization": f"Bearer {token_b}"})
    r = client.get(f"/v1/doctor/patients/{me_b['patient_id']}/timeline", headers={"Authorization": f"Bearer {token_doc}"})
    assert r.status_code == 403


def test_invalid_login_uses_error_envelope():
    r = client.post("/v1/auth/login", json={"email": "missing@demo.medivault", "password": "wrongpass1"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def _sample_pdf_bytes() -> bytes:
    sample = Path(__file__).resolve().parents[2] / "samples" / "demo-lab-report.txt"
    text = sample.read_text()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in text.splitlines():
        pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


def test_upload_extracts_named_labs_and_fhir():
    token = _login("a@demo.medivault")
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("lab.pdf", _sample_pdf_bytes(), "application/pdf")}
    uploaded = client.post("/v1/documents/upload", headers=headers, files=files)
    assert uploaded.status_code == 200, uploaded.text
    doc_id = uploaded.json()["id"]

    status = client.get(f"/v1/documents/{doc_id}", headers=headers)
    assert status.json()["processing_status"] == "validated"

    timeline = client.get("/v1/records/timeline", headers=headers).json()
    names = {item["display_name"] for item in timeline["items"]}
    types = {item["type"] for item in timeline["items"]}
    assert "HbA1c" in names
    assert "Blood Pressure" in names
    assert "Metformin" in names
    assert "allergy" in types
    hba1c = next(item for item in timeline["items"] if item["display_name"] == "HbA1c")
    assert hba1c["interpretation"] == "high"

    summary = client.get("/v1/records/summary", headers=headers).json()
    assert summary["counts"]["observations"] >= 2
    assert summary["counts"]["allergies"] >= 1

    fhir = client.get("/v1/records/fhir", headers=headers).json()
    assert fhir["resourceType"] == "Bundle"
    resource_types = {entry["resource"]["resourceType"] for entry in fhir["entry"]}
    assert "Patient" in resource_types
    assert "Observation" in resource_types
    assert "AllergyIntolerance" in resource_types

    duplicate = client.post("/v1/documents/upload", headers=headers, files=files)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE_DOCUMENT"


def test_doctor_scope_filters_record_types():
    token_a = _login("a@demo.medivault")
    token_doc = _login("doctor@demo.medivault")
    me_a = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"}).json()
    me_doc = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token_doc}"}).json()
    exp = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    client.post(
        "/v1/consents",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "doctor_id": me_doc["doctor_id"],
            "scope": {"record_types": ["observations"]},
            "permissions": ["read"],
            "expires_at": exp,
        },
    )
    r = client.get(f"/v1/doctor/patients/{me_a['patient_id']}/timeline", headers={"Authorization": f"Bearer {token_doc}"})
    assert r.status_code == 200
    types = {item["type"] for item in r.json()["items"]}
    assert types <= {"observation"}


def test_extractor_parses_sample_text():
    text = Path(__file__).resolve().parents[2] / "samples" / "demo-lab-report.txt"
    data = mock_structured_extraction(text.read_text())
    assert data["hospital"] == "City General Hospital"
    assert data["laboratory_results"][0]["display_name"] == "HbA1c"
    assert data["vitals"][0]["display_name"] == "Blood Pressure"
    assert data["medications"][0]["dosage"] == "500mg"
    assert data["allergies"]
    assert data["confidence"] > 0.7
