import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import log_with_fields
from app.models.catalog import Doctor, Treatment
from app.models.clinic import Clinic, ClinicLocation
from app.providers.embeddings import get_embedding_provider
from app.providers.llm import get_llm_provider
from app.providers.llm.ollama import OllamaError
from app.repositories import knowledge as knowledge_repo
from app.utils.chunking import chunk_text

logger = logging.getLogger("cosmopilot.knowledge")

# Below this cosine similarity, retrieved content is considered too weak to
# ground an answer in — CLAUDE.md §25: don't fabricate, degrade gracefully
# and hand off instead. Chosen empirically for bge-small-en-v1.5's typical
# score range on short passages, not a universal constant for every model.
MIN_SIMILARITY = 0.45
MAX_SEARCH_RESULTS = 4
MAX_CONTEXT_CHARS = 2500

# Phase 5 originally shipped with llama3 (8B) and this capped at 1 — that
# model reliably REFUSED once a second chunk was added to context (see git
# history), even when the answer was clearly present. Phase 6 switched the
# default Ollama model to qwen2.5:7b (llama3 doesn't support tool calling
# at all, which the AI Concierge needs) — re-tested and qwen2.5 handles
# multi-chunk context correctly, so this goes back up to match
# MAX_SEARCH_RESULTS. If a future model regresses on this, re-verify
# empirically before assuming this constant is still safe.
MAX_LLM_CONTEXT_CHUNKS = MAX_SEARCH_RESULTS

SYSTEM_PROMPT_TEMPLATE = (
    "You are the approved-knowledge assistant for {clinic_name}, a cosmetic dental clinic. "
    "Answer the question using ONLY the information in the provided context. "
    "Do not add any fact, price, credential, or claim that is not explicitly present in the "
    "context. If the context does not contain the answer, say exactly: "
    '"I don\'t have approved information to answer that." '
    "Never diagnose, give medical advice, or guarantee outcomes. Keep answers brief and factual."
)


@dataclass(frozen=True)
class KnowledgeSource:
    title: str | None
    source_type: str
    similarity: float
    excerpt: str


@dataclass(frozen=True)
class KnowledgeAnswer:
    answer: str
    grounded: bool
    generated: bool
    sources: list[KnowledgeSource]


def has_sufficient_knowledge(
    best_similarity: float | None, threshold: float = MIN_SIMILARITY
) -> bool:
    return best_similarity is not None and best_similarity >= threshold


async def _embed_and_store(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    items: list[dict],
) -> int:
    """`items`: [{source_type, source_id, document_id, title, content}, ...]"""
    if not items:
        return 0
    provider = get_embedding_provider()
    vectors = await provider.embed([item["content"] for item in items])
    for item, vector in zip(items, vectors, strict=True):
        await knowledge_repo.create_chunk(
            db,
            clinic_id=clinic_id,
            content=item["content"],
            embedding=vector,
            source_type=item["source_type"],
            source_id=item.get("source_id"),
            document_id=item.get("document_id"),
            title=item.get("title"),
        )
    return len(items)


def _join_sentences(parts: list[str]) -> str:
    """Joins parts as sentences without doubling punctuation — most of our
    structured fields (description, approved_information, FAQ answers)
    already end in a period, so a plain ". ".join produced "..." runs that
    made the context look malformed and made the local LLM needlessly
    cautious about trusting it."""
    return " ".join(p.strip().rstrip(".") + "." for p in parts if p.strip())


def _clinic_chunks(clinic: Clinic) -> list[dict]:
    parts = [clinic.name]
    if clinic.description:
        parts.append(clinic.description)
    contact = ", ".join(p for p in [clinic.primary_phone, clinic.email, clinic.website] if p)
    if contact:
        parts.append(f"Contact: {contact}")
    return [
        {
            "source_type": "clinic",
            "source_id": clinic.id,
            "title": clinic.name,
            "content": " ".join(parts),
        }
    ]


def _location_chunks(clinic_name: str, locations: list[ClinicLocation]) -> list[dict]:
    chunks = []
    for location in locations:
        parts = [f"{clinic_name} location:"]
        address = ", ".join(p for p in [location.address, location.city, location.country] if p)
        if address:
            parts.append(address)
        if location.phone:
            parts.append(f"Phone: {location.phone}")
        if location.opening_hours:
            hours = "; ".join(f"{day}: {hrs}" for day, hrs in location.opening_hours.items())
            parts.append(f"Opening hours: {hours}")
        chunks.append(
            {
                "source_type": "location",
                "source_id": location.id,
                "title": f"{clinic_name} — Location",
                "content": " ".join(parts),
            }
        )
    return chunks


def _doctor_chunks(doctors: list[Doctor]) -> list[dict]:
    chunks = []
    for doctor in doctors:
        parts = [doctor.name]
        if doctor.title:
            parts.append(doctor.title)
        if doctor.specialties:
            parts.append(f"Specialties: {', '.join(doctor.specialties)}")
        if doctor.credentials:
            parts.append(doctor.credentials)
        if doctor.bio:
            parts.append(doctor.bio)
        chunks.append(
            {
                "source_type": "doctor",
                "source_id": doctor.id,
                "title": doctor.name,
                "content": _join_sentences(parts),
            }
        )
    return chunks


def _treatment_chunks(treatments: list[Treatment]) -> list[dict]:
    chunks = []
    for treatment in treatments:
        overview_parts = [treatment.name]
        if treatment.category:
            overview_parts.append(f"Category: {treatment.category}")
        if treatment.description:
            overview_parts.append(treatment.description)
        if treatment.approved_information:
            overview_parts.append(treatment.approved_information)
        if treatment.price_guidance:
            overview_parts.append(treatment.price_guidance)
        if treatment.duration:
            overview_parts.append(f"Duration: {treatment.duration}")
        chunks.append(
            {
                "source_type": "treatment",
                "source_id": treatment.id,
                "title": treatment.name,
                "content": _join_sentences(overview_parts),
            }
        )
        for faq_item in treatment.faq or []:
            question = faq_item.get("q")
            answer = faq_item.get("a")
            if not question or not answer:
                continue
            chunks.append(
                {
                    "source_type": "treatment",
                    "source_id": treatment.id,
                    "title": f"{treatment.name} — FAQ",
                    "content": f"{treatment.name}. Q: {question} A: {answer}",
                }
            )
    return chunks


async def sync_clinic_knowledge(db: AsyncSession, clinic_id: uuid.UUID) -> int:
    """
    Regenerates every auto-derived chunk (clinic/location/doctor/treatment)
    from the clinic's current structured data — the primary knowledge
    source until real uploaded documents exist (CLAUDE.md §11). Wholesale
    delete-then-recreate per source_type, not diffed — simple and correct
    at this data volume; revisit if a clinic's catalog ever gets large
    enough for this to matter.
    """
    clinic = await db.get(Clinic, clinic_id)
    if clinic is None:
        return 0

    locations = (
        (await db.execute(select(ClinicLocation).where(ClinicLocation.clinic_id == clinic_id)))
        .scalars()
        .all()
    )
    doctors = (
        (
            await db.execute(
                select(Doctor).where(Doctor.clinic_id == clinic_id, Doctor.status == "active")
            )
        )
        .scalars()
        .all()
    )
    treatments = (
        (
            await db.execute(
                select(Treatment).where(
                    Treatment.clinic_id == clinic_id, Treatment.status == "active"
                )
            )
        )
        .scalars()
        .all()
    )

    for source_type in ("clinic", "location", "doctor", "treatment"):
        await knowledge_repo.delete_chunks_by_source_type(db, clinic_id, source_type)

    items = (
        _clinic_chunks(clinic)
        + _location_chunks(clinic.name, list(locations))
        + _doctor_chunks(list(doctors))
        + _treatment_chunks(list(treatments))
    )
    count = await _embed_and_store(db, clinic_id, items)
    log_with_fields(
        logger, logging.INFO, "knowledge_synced", clinic_id=str(clinic_id), chunks=count
    )
    return count


async def ingest_document(
    db: AsyncSession, clinic_id: uuid.UUID, type_: str, title: str, text: str
) -> tuple[uuid.UUID, int]:
    document = await knowledge_repo.create_document(db, clinic_id, type_, title, text)
    await knowledge_repo.set_document_status(db, document, "processing")

    try:
        chunks = chunk_text(text)
        items = [
            {
                "source_type": "document",
                "document_id": document.id,
                "title": title,
                "content": chunk,
            }
            for chunk in chunks
        ]
        count = await _embed_and_store(db, clinic_id, items)
        await knowledge_repo.set_document_status(db, document, "completed")
    except Exception:
        await knowledge_repo.set_document_status(db, document, "failed")
        raise
    return document.id, count


async def search_clinic_knowledge(
    db: AsyncSession, clinic_id: uuid.UUID, query: str, top_k: int = MAX_SEARCH_RESULTS
) -> list[KnowledgeSource]:
    provider = get_embedding_provider()
    [query_vector] = await provider.embed([query])
    results = await knowledge_repo.search_chunks(db, clinic_id, query_vector, limit=top_k)
    return [
        KnowledgeSource(
            title=chunk.title,
            source_type=chunk.source_type,
            similarity=round(1 - distance, 4),
            excerpt=chunk.content,
        )
        for chunk, distance in results
    ]


async def answer_from_knowledge(
    db: AsyncSession, clinic_id: uuid.UUID, clinic_name: str, question: str
) -> KnowledgeAnswer:
    """
    The "approved answer system" (CLAUDE.md Phase 5) — retrieval with a
    similarity-threshold guardrail, then an LLM synthesizes a natural-
    language answer strictly from the retrieved context. Falls back to
    returning the raw top chunk (never inventing text) if generation
    itself fails, e.g. Ollama isn't running.
    """
    sources = await search_clinic_knowledge(db, clinic_id, question)
    best_similarity = sources[0].similarity if sources else None

    if not has_sufficient_knowledge(best_similarity):
        return KnowledgeAnswer(
            answer=(
                "I don't have approved information to answer that. "
                "I'll have the clinic follow up with you directly."
            ),
            grounded=False,
            generated=False,
            sources=[],
        )

    context = ""
    used_sources: list[KnowledgeSource] = []
    for source in sources[:MAX_LLM_CONTEXT_CHUNKS]:
        candidate = f"{context}\n\n{source.excerpt}".strip() if context else source.excerpt
        if len(candidate) > MAX_CONTEXT_CHARS:
            break
        context = candidate
        used_sources.append(source)

    system = SYSTEM_PROMPT_TEMPLATE.format(clinic_name=clinic_name)
    llm = get_llm_provider()
    try:
        response = await llm.generate(system=system, context=context, question=question)
        return KnowledgeAnswer(
            answer=response.text, grounded=True, generated=True, sources=used_sources
        )
    except OllamaError as exc:
        log_with_fields(
            logger,
            logging.WARNING,
            "llm_generation_failed_falling_back_to_raw_context",
            clinic_id=str(clinic_id),
            error=str(exc),
        )
        return KnowledgeAnswer(
            answer=used_sources[0].excerpt, grounded=True, generated=False, sources=used_sources
        )
