"""Document API routes."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import Session, select

from app.api.dependencies import get_db
from app.core.logging import get_logger
from app.db.models import Document, DocumentStatus, Trait
from app.schemas.document import DocumentBase, DocumentDetail, DocumentList
from app.schemas.job import JobStatus
from app.schemas.trait import TraitRead
from app.services import document_service, job_service, storage_service
from app.workers.tasks import process_document_task

router = APIRouter()
logger = get_logger(__name__)


def _document_to_base(document: Document) -> DocumentBase:
    return DocumentBase(
        id=document.id,
        title=document.title,
        original_filename=document.original_filename,
        status=document.status,
        page_count=document.page_count,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def _trait_to_schema(trait: Trait) -> TraitRead:
    return TraitRead(
        id=trait.id,
        trait_type=trait.trait_type,
        value=trait.value,
        details=trait.details,
        confidence=trait.confidence,
        pages=trait.pages,
        evidence=trait.evidence,
        created_at=trait.created_at,
        updated_at=trait.updated_at,
    )


def _document_to_detail(document: Document, traits: list[Trait]) -> DocumentDetail:
    return DocumentDetail(
        **_document_to_base(document).model_dump(),
        token_count=document.token_count,
        language=document.language,
        traits=[_trait_to_schema(trait) for trait in traits],
    )


@router.post("/", response_model=DocumentDetail, status_code=201)
async def upload_document(
    file: UploadFile,
    session: Session = Depends(get_db),
) -> DocumentDetail:
    """Upload a PDF and create a document record."""

    stored_filename, path = storage_service.save_upload(file)
    document = document_service.create_document(
        session,
        original_filename=file.filename or stored_filename,
        stored_filename=stored_filename,
        source_path=path,
    )
    traits: list[Trait] = []
    logger.info("Uploaded document %s", document.id)
    return _document_to_detail(document, traits)


@router.get("/", response_model=DocumentList)
def list_documents(
    skip: int = 0,
    limit: int = 50,
    session: Session = Depends(get_db),
) -> DocumentList:
    items, total = document_service.list_documents(session, offset=skip, limit=limit)
    return DocumentList(items=[_document_to_base(doc) for doc in items], total=total)


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document_detail(document_id: uuid.UUID, session: Session = Depends(get_db)) -> DocumentDetail:
    document = document_service.get_document(session, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    traits = session.exec(select(Trait).where(Trait.document_id == document.id)).all()
    return _document_to_detail(document, traits)


@router.post("/{document_id}/process", response_model=JobStatus)
def process_document(document_id: uuid.UUID, session: Session = Depends(get_db)) -> JobStatus:
    document = document_service.get_document(session, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status in {DocumentStatus.IN_FLIGHT, DocumentStatus.PROCESSING}:
        raise HTTPException(status_code=409, detail="Document already queued for processing")

    document_service.mark_in_flight(session, document)
    task = process_document_task.delay(str(document.id))
    job = job_service.create_job(session, document_id=document.id, task_id=task.id)
    return JobStatus(
        id=job.id,
        document_id=document.id,
        status=job.status,
        step=job.step,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )
