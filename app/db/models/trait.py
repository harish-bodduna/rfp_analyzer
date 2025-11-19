"""Trait model."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, JSON
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel


TRAIT_TYPES = [
    "title",
    "due_date",
    "point_of_contact",
    "submitted_to",
    "submission_method",
    "submission_checklist",
    "questions_poc",
    "receipt_of_amendments",
    "notary_needed",
    "resumes_needed",
    "references_needed",
    "scope_of_work",
    "categorization",
    "insurance_needed",
    "technical_requirements",
]


class Trait(SQLModel, table=True):
    """Stores extracted trait values."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="document.id", index=True)
    trait_type: str = Field(index=True)

    value: str | None = Field(default=None)
    details: dict | None = Field(default=None, sa_column=Column(JSON))
    confidence: float | None = Field(default=None)
    pages: list[int] | None = Field(default=None, sa_column=Column(JSON))
    evidence: list[str] | None = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    document: "Document" | None = Relationship(
        sa_relationship=relationship("Document", back_populates="traits")
    )
