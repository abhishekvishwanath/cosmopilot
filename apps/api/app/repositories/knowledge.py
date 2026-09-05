import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.knowledge_chunk import KnowledgeChunk


async def create_document(
    db: AsyncSession, clinic_id: uuid.UUID, type_: str, title: str, extracted_text: str
) -> Document:
    document = Document(
        clinic_id=clinic_id,
        type=type_,
        title=title,
        extracted_text=extracted_text,
        embedding_status="pending",
    )
    db.add(document)
    await db.flush()
    return document


async def list_documents(db: AsyncSession, clinic_id: uuid.UUID) -> list[Document]:
    result = await db.execute(
        select(Document).where(Document.clinic_id == clinic_id).order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def set_document_status(db: AsyncSession, document: Document, status: str) -> Document:
    document.embedding_status = status
    await db.flush()
    return document


async def delete_chunks_by_source_type(
    db: AsyncSession, clinic_id: uuid.UUID, source_type: str
) -> None:
    await db.execute(
        delete(KnowledgeChunk).where(
            KnowledgeChunk.clinic_id == clinic_id, KnowledgeChunk.source_type == source_type
        )
    )


async def delete_chunks_for_document(db: AsyncSession, document_id: uuid.UUID) -> None:
    await db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id))


async def create_chunk(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    content: str,
    embedding: list[float],
    source_type: str,
    source_id: uuid.UUID | None = None,
    document_id: uuid.UUID | None = None,
    title: str | None = None,
) -> KnowledgeChunk:
    chunk = KnowledgeChunk(
        clinic_id=clinic_id,
        source_type=source_type,
        source_id=source_id,
        document_id=document_id,
        title=title,
        content=content,
        embedding=embedding,
    )
    db.add(chunk)
    await db.flush()
    return chunk


async def search_chunks(
    db: AsyncSession, clinic_id: uuid.UUID, query_embedding: list[float], limit: int = 5
) -> list[tuple[KnowledgeChunk, float]]:
    """Returns (chunk, cosine_distance) pairs, closest first. Similarity is
    1 - distance for callers that want it framed as a score."""
    distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)
    query = (
        select(KnowledgeChunk, distance.label("distance"))
        .where(KnowledgeChunk.clinic_id == clinic_id)
        .order_by(distance)
        .limit(limit)
    )
    result = await db.execute(query)
    return [(row[0], row[1]) for row in result.all()]
