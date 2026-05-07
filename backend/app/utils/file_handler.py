from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import UploadFile

from app.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".md", ".markdown", ".txt", ".text"}


async def save_upload(file: UploadFile, project_id: str) -> tuple[str, str]:
    """Save an uploaded file to disk. Returns (file_path, content_hash)."""
    upload_dir = Path(settings.UPLOAD_DIR) / project_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename
    content = await file.read()

    content_hash = hashlib.sha256(content).hexdigest()

    with open(file_path, "wb") as f:
        f.write(content)

    return str(file_path), content_hash


def validate_file(file: UploadFile) -> None:
    """Validate file extension and size."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {suffix}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if file.size and file.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(
            f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB} MB"
        )
