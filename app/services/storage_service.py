"""File storage utilities."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


def ensure_directories() -> None:
    """Create storage directories if they do not exist."""

    for directory in (settings.raw_files_dir, settings.processed_files_dir, settings.uploaded_files_dir):
        Path(directory).mkdir(parents=True, exist_ok=True)


def save_upload(upload: UploadFile) -> tuple[str, str]:
    """Persist uploaded file to disk with UUID-based filename.

    Returns tuple of (stored_filename, absolute_path).
    """

    ensure_directories()
    suffix = Path(upload.filename or "document.pdf").suffix or ".pdf"
    stored_filename = f"{uuid.uuid4()}{suffix}"
    destination = Path(settings.raw_files_dir) / stored_filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    return stored_filename, str(destination)
