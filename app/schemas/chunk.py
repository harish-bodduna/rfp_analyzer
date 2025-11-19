"""Chunk schemas."""
from uuid import UUID

from pydantic import BaseModel


class ChunkRead(BaseModel):
    id: UUID
    section_id: UUID | None = None
    page_start: int
    page_end: int
    token_count: int
    summary: str | None = None
    keywords: list[str] | None = None
