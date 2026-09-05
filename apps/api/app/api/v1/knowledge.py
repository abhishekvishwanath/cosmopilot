from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ClinicPrincipal, get_current_clinic_staff
from app.db.session import get_db
from app.repositories import clinics as clinics_repo
from app.repositories import knowledge as knowledge_repo
from app.schemas.knowledge import (
    DocumentIngestRequest,
    DocumentIngestResult,
    DocumentRead,
    KnowledgeAnswerRead,
    KnowledgeAskRequest,
    KnowledgeSourceRead,
    SyncResult,
)
from app.services import knowledge as knowledge_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/sync", response_model=SyncResult)
async def sync_knowledge(
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SyncResult:
    count = await knowledge_service.sync_clinic_knowledge(db, principal.clinic_id)
    await db.commit()
    return SyncResult(chunks_created=count)


@router.get("/documents", response_model=list[DocumentRead])
async def list_documents(
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DocumentRead]:
    documents = await knowledge_repo.list_documents(db, principal.clinic_id)
    return [DocumentRead.model_validate(d) for d in documents]


@router.post("/documents", response_model=DocumentIngestResult, status_code=201)
async def ingest_document(
    payload: DocumentIngestRequest,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentIngestResult:
    document_id, count = await knowledge_service.ingest_document(
        db, principal.clinic_id, payload.type, payload.title, payload.text
    )
    await db.commit()
    return DocumentIngestResult(document_id=document_id, chunks_created=count)


@router.post("/ask", response_model=KnowledgeAnswerRead)
async def ask_knowledge(
    payload: KnowledgeAskRequest,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> KnowledgeAnswerRead:
    clinic = await clinics_repo.get_clinic(db, principal.clinic_id)
    clinic_name = clinic.name if clinic else "the clinic"
    result = await knowledge_service.answer_from_knowledge(
        db, principal.clinic_id, clinic_name, payload.question
    )
    return KnowledgeAnswerRead(
        answer=result.answer,
        grounded=result.grounded,
        generated=result.generated,
        sources=[
            KnowledgeSourceRead(
                title=s.title, source_type=s.source_type, similarity=s.similarity, excerpt=s.excerpt
            )
            for s in result.sources
        ],
    )
