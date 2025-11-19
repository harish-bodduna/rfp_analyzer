"""Document model."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, JSON
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel


class DocumentStatus:
    UPLOADED = "uploaded"
    IN_FLIGHT = "in_flight"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(SQLModel, table=True):
    """Represents an uploaded RFP/RFQ document."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    title: str | None = Field(default=None)
    original_filename: str = Field(index=True)
    stored_filename: str = Field(index=True)
    source_path: str = Field()
    status: str = Field(default=DocumentStatus.UPLOADED, index=True)

    page_count: int = Field(default=0)
    token_count: int = Field(default=0)
    language: str | None = Field(default=None)

    metadata_json: dict | None = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    sections: list["Section"] = Relationship(
        sa_relationship=relationship("Section", back_populates="document")
    )
    chunks: list["Chunk"] = Relationship(
        sa_relationship=relationship("Chunk", back_populates="document")
    )
    traits: list["Trait"] = Relationship(
        sa_relationship=relationship("Trait", back_populates="document")
    )
    jobs: list["ProcessingJob"] = Relationship(
        sa_relationship=relationship("ProcessingJob", back_populates="document")
    )
