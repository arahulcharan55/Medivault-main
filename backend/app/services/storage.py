import hashlib
import secrets
from io import BytesIO
from pathlib import Path

import aiofiles
from pypdf import PdfReader

from app.config import settings

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def ensure_storage_root() -> Path:
    root = Path(settings.storage_path)
    root.mkdir(parents=True, exist_ok=True)
    return root


def validate_upload(mime_type: str, file_size: int) -> None:
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Unsupported file type")
    if file_size <= 0 or file_size > settings.max_upload_bytes:
        raise ValueError("Invalid file size")


def build_object_key(patient_id: str, document_id: str, content_hash: str, mime_type: str) -> str:
    ext = ALLOWED_MIME_TYPES[mime_type]
    return f"{patient_id}/{document_id}/{content_hash}{ext}"


def compute_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


async def save_document(content: bytes, storage_path: str) -> None:
    full_path = ensure_storage_root() / storage_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(full_path, "wb") as f:
        await f.write(content)


def read_document_bytes(storage_path: str) -> bytes:
    full_path = ensure_storage_root() / storage_path
    return full_path.read_bytes()


def extract_text_from_document(content: bytes, mime_type: str) -> str:
    if mime_type == "application/pdf":
        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    if mime_type.startswith("image/"):
        return "[image document uploaded — OCR provider required for image text in production]"
    return content.decode("utf-8", errors="ignore")


from app.services.extractor import mock_structured_extraction, validate_extraction_schema  # noqa: F401


def generate_token_identifier() -> str:
    return secrets.token_urlsafe(24)
