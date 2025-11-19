"""Trait schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TraitRead(BaseModel):
    id: UUID
    trait_type: str
    value: str | None = None
    details: dict | None = None
    confidence: float | None = None
    pages: list[int] | None = None
    evidence: list[str] | None = None
    created_at: datetime
    updated_at: datetime


class TraitCreate(BaseModel):
    trait_type: str
    value: str | None = None
    details: dict | None = Field(default_factory=dict)
    confidence: float | None = None
    pages: list[int] | None = None
    evidence: list[str] | None = None
