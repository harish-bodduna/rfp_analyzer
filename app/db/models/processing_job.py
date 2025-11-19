"""Processing job status model."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel


class ProcessingStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ProcessingJob(SQLModel, table=True):
    """Tracks Celery job state for a document."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="document.id", index=True)
    task_id: str | None = Field(default=None, index=True)
    status: str = Field(default=ProcessingStatus.PENDING, index=True)
    step: str | None = Field(default=None)
    error_message: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    document: "Document" | None = Relationship(
        sa_relationship=relationship("Document", back_populates="jobs")
    )
