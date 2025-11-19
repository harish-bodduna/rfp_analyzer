"""Service helpers for document records."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, select

from app.db.models import Document, DocumentStatus


def list_documents(session: Session, offset: int = 0, limit: int = 50) -> tuple[list[Document], int]:
    """Return paginated documents and total count."""

    statement = select(Document).offset(offset).limit(limit).order_by(Document.created_at.desc())
    items = session.exec(statement).all()
    total = session.exec(select(func.count()).select_from(Document)).one()
    return items, int(total)


def get_document(session: Session, document_id: uuid.UUID) -> Document | None:
    """Fetch a single document by id."""

    return session.get(Document, document_id)


def create_document(
    session: Session,
    *,
    original_filename: str,
    stored_filename: str,
    source_path: str,
    title: str | None = None,
    page_count: int | None = None,
    token_count: int | None = None,
    language: str | None = None,
    metadata_json: dict | None = None,
) -> Document:
    """Create and persist a new document record."""

    document = Document(
        title=title,
        original_filename=original_filename,
        stored_filename=stored_filename,
        source_path=source_path,
        page_count=page_count or 0,
        token_count=token_count or 0,
        language=language,
        metadata_json=metadata_json,
    )
    session.add(document)
    session.flush()
    return document


def update_document_status(
    session: Session,
    document: Document,
    *,
    status: str,
    metadata_updates: dict | None = None,
) -> Document:
    """Update document status and metadata."""

    document.status = status
    document.updated_at = datetime.utcnow()
    if metadata_updates:
        base = document.metadata_json or {}
        base.update(metadata_updates)
        document.metadata_json = base
    session.add(document)
    session.flush()
    return document


def mark_processing(session: Session, document: Document) -> Document:
    """Convenience to mark as processing."""

    return update_document_status(session, document, status=DocumentStatus.PROCESSING)


def mark_in_flight(session: Session, document: Document) -> Document:
    """Convenience to mark as queued for processing."""

    return update_document_status(session, document, status=DocumentStatus.IN_FLIGHT)


def mark_completed(session: Session, document: Document) -> Document:
    """Convenience to mark as completed."""

    return update_document_status(session, document, status=DocumentStatus.COMPLETED)


def mark_failed(session: Session, document: Document, error: str | None = None) -> Document:
    """Convenience to mark as failed."""

    metadata = {"error": error} if error else None
    return update_document_status(session, document, status=DocumentStatus.FAILED, metadata_updates=metadata)
