"""Processing job schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobStatus(BaseModel):
    id: UUID
    document_id: UUID
    status: str
    step: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
