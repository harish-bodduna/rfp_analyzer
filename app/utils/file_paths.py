"""Helpers for constructing document-specific paths."""
from __future__ import annotations

from pathlib import Path
from uuid import UUID

from app.core.config import settings


def document_processed_dir(document_id: UUID) -> Path:
    path = Path(settings.processed_files_dir) / str(document_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def document_chunks_path(document_id: UUID) -> Path:
    return document_processed_dir(document_id) / "chunks.json"
