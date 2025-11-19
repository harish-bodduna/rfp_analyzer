"""Processing job helpers."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Session

from app.db.models import ProcessingJob, ProcessingStatus


def create_job(session: Session, document_id: uuid.UUID, task_id: str | None = None) -> ProcessingJob:
    job = ProcessingJob(document_id=document_id, task_id=task_id)
    session.add(job)
    session.flush()
    return job


def update_job(
    session: Session,
    job: ProcessingJob,
    *,
    status: str | None = None,
    step: str | None = None,
    error: str | None = None,
) -> ProcessingJob:
    if status:
        job.status = status
        if status == ProcessingStatus.RUNNING:
            job.started_at = datetime.utcnow()
        if status in {ProcessingStatus.SUCCESS, ProcessingStatus.FAILED}:
            job.completed_at = datetime.utcnow()
    if step:
        job.step = step
    if error:
        job.error_message = error
    session.add(job)
    session.flush()
    return job
