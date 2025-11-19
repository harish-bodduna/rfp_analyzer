"""Chunk model."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, JSON
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel


class Chunk(SQLModel, table=True):
    """Represents a chunk of document text and metadata."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="document.id", index=True)
    section_id: uuid.UUID | None = Field(default=None, foreign_key="section.id", index=True)

    page_start: int = Field(default=1)
    page_end: int = Field(default=1)
    token_count: int = Field(default=0)
    content: str = Field()
    summary: str | None = Field(default=None)

    keywords: list[str] | None = Field(default=None, sa_column=Column(JSON))
    embedding_id: str | None = Field(default=None)
    embedding: list[float] | None = Field(default=None, sa_column=Column(JSON))
    metadata_json: dict | None = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)

    document: "Document" | None = Relationship(
        sa_relationship=relationship("Document", back_populates="chunks")
    )
    section: "Section" | None = Relationship(
        sa_relationship=relationship("Section", back_populates="chunks")
    )
