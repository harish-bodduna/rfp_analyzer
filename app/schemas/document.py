"""Document schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.trait import TraitRead


class DocumentBase(BaseModel):
    id: UUID
    title: str | None = None
    original_filename: str
    status: str
    page_count: int | None = None
    created_at: datetime
    updated_at: datetime


class DocumentDetail(DocumentBase):
    token_count: int | None = None
    language: str | None = None
    traits: list[TraitRead] | None = None


class DocumentList(BaseModel):
    items: list[DocumentBase]
    total: int
