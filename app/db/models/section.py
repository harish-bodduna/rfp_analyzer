"""Section model."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, JSON
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel


class Section(SQLModel, table=True):
    """Logical section/subsection metadata."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="document.id", index=True)
    parent_id: uuid.UUID | None = Field(default=None, foreign_key="section.id")

    title: str | None = Field(default=None)
    section_path: str | None = Field(default=None, index=True)
    level: int = Field(default=0)

    page_start: int | None = Field(default=None)
    page_end: int | None = Field(default=None)
    token_count: int = Field(default=0)

    metadata_json: dict | None = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)

    document: "Document" | None = Relationship(
        sa_relationship=relationship("Document", back_populates="sections")
    )
    parent: "Section" | None = Relationship(
        sa_relationship=relationship(
            "Section",
            remote_side="Section.id",
        )
    )
    chunks: list["Chunk"] = Relationship(
        sa_relationship=relationship("Chunk", back_populates="section")
    )
