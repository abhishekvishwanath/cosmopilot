import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPkMixin

# bge-small-en-v1.5 (fastembed) — 384 dimensions. Changing embedding models
# means re-embedding everything and changing this constant + the migration.
EMBEDDING_DIMENSIONS = 384

KNOWLEDGE_SOURCE_TYPES = ("clinic", "location", "doctor", "treatment", "document")
KnowledgeSourceType = Enum(*KNOWLEDGE_SOURCE_TYPES, name="knowledge_source_type")


class KnowledgeChunk(Base, UUIDPkMixin):
    """
    One retrievable, embedded passage (CLAUDE.md §11's RAG pipeline).
    `source_type`/`source_id` point back at the structured row a chunk was
    generated from (clinic/location/doctor/treatment) for chunks produced
    by sync_clinic_knowledge(); `document_id` is set instead for chunks
    from an uploaded Document. source_id isn't a DB foreign key — it's
    polymorphic across several tables, same pattern as
    ClinicStaff.user_id (see models/clinic.py) for a cross-table reference
    the ORM can't type as one FK. Append-only-ish: resynced wholesale
    rather than diffed, so no updated_at.
    """

    __tablename__ = "knowledge_chunks"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(KnowledgeSourceType, nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
