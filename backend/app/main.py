from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine, ensure_sqlite_columns
from app.models import AllergyIntolerance  # noqa: F401 — register metadata
from app.routers import audit, auth, consents, doctor, doctors, documents, patients, processing, records

Base.metadata.create_all(bind=engine)
ensure_sqlite_columns()
Path(settings.storage_path).mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="MediVault API",
    version="0.2.0",
    description="Patient-controlled digital health records with consent, extraction, and FHIR export.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID", str(uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", str(uuid4()))
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        payload = {
            "code": detail.get("code"),
            "message": detail.get("message", "Request failed"),
            "request_id": request_id,
        }
        extra = {k: v for k, v in detail.items() if k not in {"code", "message"}}
        payload.update(extra)
        return JSONResponse(status_code=exc.status_code, content={"error": payload})
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(detail), "request_id": request_id}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "request_id": getattr(request.state, "request_id", str(uuid4())),
            }
        },
    )


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment, "version": "0.2.0"}


app.include_router(auth.router, prefix="/v1")
app.include_router(patients.router, prefix="/v1")
app.include_router(doctors.router, prefix="/v1")
app.include_router(documents.router, prefix="/v1")
app.include_router(records.router, prefix="/v1")
app.include_router(consents.router, prefix="/v1")
app.include_router(audit.router, prefix="/v1")
app.include_router(processing.router, prefix="/v1")
app.include_router(doctor.router, prefix="/v1")
