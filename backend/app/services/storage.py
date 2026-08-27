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

# Browsers and some operating systems send a generic content type (or none) for
# perfectly valid PDFs/images, especially on drag-and-drop uploads. Fall back to
# the filename extension and content sniffing before rejecting the upload.
_EXTENSION_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}
_GENERIC_MIME_TYPES = {"", "application/octet-stream", "binary/octet-stream"}


def _sniff_mime_type(content: bytes) -> str | None:
    if content.startswith(b"%PDF-"):
        return "application/pdf"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return None


def resolve_mime_type(declared: str | None, filename: str | None, content: bytes = b"") -> str:
    """Best-effort content type for an upload.

    Trusts the client's content type when it is one we accept, otherwise derives
    it from the filename extension or the file's magic bytes.
    """
    declared = (declared or "").split(";")[0].strip().lower()
    if declared in ALLOWED_MIME_TYPES:
        return declared

    ext = Path(filename or "").suffix.lower()
    if declared in _GENERIC_MIME_TYPES and ext in _EXTENSION_MIME_TYPES:
        return _EXTENSION_MIME_TYPES[ext]

    sniffed = _sniff_mime_type(content)
    if sniffed:
        return sniffed
    if ext in _EXTENSION_MIME_TYPES:
        return _EXTENSION_MIME_TYPES[ext]
    return declared or "application/octet-stream"


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
