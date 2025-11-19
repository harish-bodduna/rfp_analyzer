"""Celery task implementations."""
from __future__ import annotations

import json
import uuid

from celery import states
from sqlmodel import delete, select

from app.core.logging import get_logger
from app.db.models import (
    Chunk,
    Document,
    ProcessingJob,
    ProcessingStatus,
    Trait,
    TRAIT_TYPES,
)
from app.db.session import get_session
from app.services import document_service, extraction_service, job_service, retrieval_service
from app.services.chunking_service import chunk_elements, chunk_pages
from app.services.embeddings_service import embed_text
from app.services.parsing_service import summarize_document
from app.utils.file_paths import document_chunks_path
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(bind=True, name="process_document")
def process_document_task(self, document_id: str) -> str:
    """Full pipeline for document processing and trait extraction."""

    logger.info("Starting processing for document %s", document_id)
    with get_session() as session:
        document = session.get(Document, uuid.UUID(document_id))
        if not document:
            logger.error("Document %s not found", document_id)
            self.update_state(state=states.FAILURE, meta={"error": "Document not found"})
            return "missing"

        job = session.exec(
            select(ProcessingJob)
            .where(ProcessingJob.document_id == document.id, ProcessingJob.task_id == self.request.id)
            .order_by(ProcessingJob.created_at.desc())
        ).first()

        try:
            document_service.mark_processing(session, document)
            if job:
                job_service.update_job(session, job, status=ProcessingStatus.RUNNING, step="parsing")
            session.commit()

            summary = summarize_document(document.source_path)
            document.page_count = summary["page_count"]
            document.token_count = summary["token_count"]
            document.metadata_json = {
                **(document.metadata_json or {}),
                "pages": summary["pages"],
                "elements_ingested": len(summary.get("elements", [])),
            }
            session.add(document)

            # Remove previous processing artifacts if they exist.
            session.exec(delete(Chunk).where(Chunk.document_id == document.id))
            session.exec(delete(Trait).where(Trait.document_id == document.id))
            session.flush()

            elements = summary.get("elements") or []
            if elements:
                chunk_payloads = chunk_elements(elements, max_tokens=900, min_tokens=120, overlap_tokens=120)
            else:
                chunk_payloads = chunk_pages(summary["pages"])

            if job:
                job_service.update_job(session, job, step="chunking")

            chunk_records: list[Chunk] = []
            for payload in chunk_payloads:
                chunk = Chunk(
                    document_id=document.id,
                    page_start=payload.page_start,
                    page_end=payload.page_end,
                    token_count=payload.token_count,
                    content=payload.content,
                    summary=payload.summary,
                    metadata_json=payload.metadata,
                )
                session.add(chunk)
                chunk_records.append(chunk)
            session.flush()

            # Persist chunk metadata for offline inspection.
            chunk_path = document_chunks_path(document.id)
            chunk_path.write_text(
                json.dumps(
                    [
                        {
                            "id": str(chunk.id),
                            "page_start": chunk.page_start,
                            "page_end": chunk.page_end,
                            "token_count": chunk.token_count,
                            "metadata": chunk.metadata_json,
                        }
                        for chunk in chunk_records
                    ],
                    indent=2,
                ),
                encoding="utf-8",
            )

            if job:
                job_service.update_job(session, job, step="embedding")

            # Generate embeddings for retrieval.
            for chunk in chunk_records:
                try:
                    chunk.embedding = embed_text(chunk.content)
                    session.add(chunk)
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.warning("Embedding generation failed for chunk %s: %s", chunk.id, exc)
            session.flush()

            if job:
                job_service.update_job(session, job, step="trait_extraction")

            traits_created = 0
            for trait_type in TRAIT_TYPES:
                context, supporting_chunks = retrieval_service.build_context_for_trait(
                    session,
                    document.id,
                    trait_type,
                    token_budget=1200,
                )
                if not context or not supporting_chunks:
                    continue
                extraction = extraction_service.extract_trait(trait_type, context)
                pages = extraction.get("pages") or sorted({chunk.page_start for chunk in supporting_chunks})
                evidence = extraction.get("evidence") or [
                    f"Pages {chunk.page_start}-{chunk.page_end}: {chunk.content[:280]}"
                    for chunk in supporting_chunks
                ]
                trait = Trait(
                    document_id=document.id,
                    trait_type=trait_type,
                    value=extraction.get("value"),
                    confidence=extraction.get("confidence"),
                    pages=pages,
                    evidence=evidence,
                    details={
                        "source_chunk_ids": [str(chunk.id) for chunk in supporting_chunks],
                        "context_preview": context[:1000],
                    },
                )
                session.add(trait)
                traits_created += 1

            session.flush()

            document.metadata_json = {
                **(document.metadata_json or {}),
                "chunk_count": len(chunk_records),
                "trait_count": traits_created,
            }
            session.add(document)

            document_service.mark_completed(session, document)
            if job:
                job_service.update_job(session, job, status=ProcessingStatus.SUCCESS, step="completed")
            logger.info("Completed processing for document %s", document_id)
            return "ok"
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Processing failed for document %s", document_id)
            document_service.mark_failed(session, document, error=str(exc))
            if job:
                job_service.update_job(session, job, status=ProcessingStatus.FAILED, error=str(exc))
            self.update_state(state=states.FAILURE, meta={"error": str(exc)})
            raise
