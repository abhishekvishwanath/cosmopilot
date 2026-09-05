import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentIngestRequest(BaseModel):
    type: str = Field(max_length=50)
    title: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1)


class DocumentIngestResult(BaseModel):
    document_id: uuid.UUID
    chunks_created: int


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    type: str
    title: str
    embedding_status: str
    created_at: datetime


class SyncResult(BaseModel):
    chunks_created: int


class KnowledgeAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class KnowledgeSourceRead(BaseModel):
    title: str | None
    source_type: str
    similarity: float
    excerpt: str


class KnowledgeAnswerRead(BaseModel):
    answer: str
    grounded: bool
    generated: bool
    sources: list[KnowledgeSourceRead]
