import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPkMixin

DOCUMENT_EMBEDDING_STATUSES = ("pending", "processing", "completed", "failed")


class Document(Base, UUIDPkMixin, TimestampMixin):
    """
    Clinic-provided knowledge source (CLAUDE.md §8, §11) — a policy sheet,
    an FAQ doc, anything the clinic hands over as text. `storage_path` is
    reserved for when real file upload (Supabase Storage) lands; Phase 5
    accepts raw text directly into `extracted_text`, since there are no
    real uploaded files yet and OCR/PDF-parsing is out of scope for the
    prototype.
    """

    __tablename__ = "documents"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(500))
    extracted_text: Mapped[str | None] = mapped_column(Text)
    embedding_status: Mapped[str] = mapped_column(String(20), server_default="pending")
