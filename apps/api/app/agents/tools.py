"""
The AI Concierge's tool set (CLAUDE.md §12). Every tool takes a
`ToolContext` carrying `clinic_id` (and `lead_id`, once known) supplied by
the server — never by the LLM — so a tool call can never read or write
outside the clinic/lead it was actually invoked for, regardless of what
arguments the model tries to pass (CLAUDE.md's "never allow the LLM to
bypass authorization").

Tools that would need real calendar/availability truth
(check_appointment_availability, book_appointment, reschedule_appointment)
are honest stubs for now — Phase 7 builds the CalendarProvider that makes
them real. Until then they say so and escalate, rather than inventing a
slot or a "booked" confirmation (CLAUDE.md §25).
"""

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.repositories import appointments as appointments_repo
from app.repositories import catalog as catalog_repo
from app.repositories import clinics as clinics_repo
from app.repositories import knowledge as knowledge_repo
from app.repositories import leads as leads_repo
from app.services import knowledge as knowledge_service
from app.services import leads as leads_service
from app.services.appointments import transition_appointment_status


@dataclass
class ToolContext:
    db: AsyncSession
    clinic_id: uuid.UUID
    clinic_name: str
    lead: Lead | None


class ToolError(Exception):
    """A tool ran but couldn't do what was asked (bad/missing input, not
    found, etc) — returned to the model as a structured error so it can
    react sensibly, never raised as an uncaught exception mid-conversation."""


def _find_treatment_by_name(treatments: list[Any], name: str) -> Any | None:
    needle = name.strip().lower()
    for t in treatments:
        if needle in t.name.lower() or t.name.lower() in needle:
            return t
    return None


def _find_doctor_by_name(doctors: list[Any], name: str) -> Any | None:
    needle = name.strip().lower()
    for d in doctors:
        if needle in d.name.lower() or d.name.lower() in needle:
            return d
    return None


async def get_clinic_details(ctx: ToolContext, **_: Any) -> dict:
    clinic = await clinics_repo.get_clinic(ctx.db, ctx.clinic_id)
    if clinic is None:
        raise ToolError("Clinic not found.")
    locations = await clinics_repo.list_locations(ctx.db, ctx.clinic_id)
    return {
        "name": clinic.name,
        "description": clinic.description,
        "phone": clinic.primary_phone,
        "email": clinic.email,
        "locations": [
            {
                "address": loc.address,
                "city": loc.city,
                "phone": loc.phone,
                "opening_hours": loc.opening_hours,
            }
            for loc in locations
        ],
    }


async def get_treatment_details(ctx: ToolContext, *, treatment_name: str, **_: Any) -> dict:
    treatments = await catalog_repo.list_active_treatments(ctx.db, ctx.clinic_id)
    treatment = _find_treatment_by_name(treatments, treatment_name)
    if treatment is None:
        raise ToolError(f"No treatment matching '{treatment_name}' found.")
    return {
        "name": treatment.name,
        "category": treatment.category,
        "description": treatment.description,
        "approved_information": treatment.approved_information,
        "duration": treatment.duration,
        "booking_enabled": treatment.booking_enabled,
    }


async def search_clinic_knowledge(ctx: ToolContext, *, query: str, **_: Any) -> dict:
    sources = await knowledge_service.search_clinic_knowledge(ctx.db, ctx.clinic_id, query)
    return {
        "results": [
            {"title": s.title, "similarity": s.similarity, "content": s.excerpt}
            for s in sources
            if knowledge_service.has_sufficient_knowledge(s.similarity)
        ]
    }


async def get_doctor_details(ctx: ToolContext, *, doctor_name: str, **_: Any) -> dict:
    doctors = await catalog_repo.list_active_doctors(ctx.db, ctx.clinic_id)
    doctor = _find_doctor_by_name(doctors, doctor_name)
    if doctor is None:
        raise ToolError(f"No doctor matching '{doctor_name}' found.")
    return {
        "name": doctor.name,
        "title": doctor.title,
        "specialties": doctor.specialties,
        "credentials": doctor.credentials,
        "bio": doctor.bio,
    }


async def get_approved_price_guidance(ctx: ToolContext, *, treatment_name: str, **_: Any) -> dict:
    treatments = await catalog_repo.list_active_treatments(ctx.db, ctx.clinic_id)
    treatment = _find_treatment_by_name(treatments, treatment_name)
    if treatment is None:
        raise ToolError(f"No treatment matching '{treatment_name}' found.")
    if not treatment.price_guidance:
        return {"price_guidance": None, "note": "No approved pricing on file for this treatment."}
    return {"price_guidance": treatment.price_guidance}


async def get_booking_policies(ctx: ToolContext, **_: Any) -> dict:
    documents = await knowledge_repo.list_documents(ctx.db, ctx.clinic_id)
    policies = [d for d in documents if d.type == "policy" and d.embedding_status == "completed"]
    if not policies:
        return {"policies": [], "note": "No booking policy documents on file."}
    return {"policies": [{"title": d.title, "text": d.extracted_text} for d in policies]}


async def create_lead(
    ctx: ToolContext,
    *,
    name: str,
    phone: str,
    treatment_name: str | None = None,
    preferred_time: str | None = None,
    consent: bool = False,
    **_: Any,
) -> dict:
    if ctx.lead is not None:
        return {"lead_id": str(ctx.lead.id), "status": ctx.lead.status, "already_existed": True}
    if not consent:
        raise ToolError("Cannot create a lead without the visitor's explicit consent.")

    treatment = None
    if treatment_name:
        treatments = await catalog_repo.list_active_treatments(ctx.db, ctx.clinic_id)
        treatment = _find_treatment_by_name(treatments, treatment_name)

    lead = await leads_service.create_lead(
        ctx.db,
        ctx.clinic_id,
        {
            "name": name,
            "phone": phone,
            "treatment_id": treatment.id if treatment else None,
            "source": "ai_concierge",
            "preferred_time": preferred_time,
            "consent": True,
        },
    )
    ctx.lead = lead
    return {"lead_id": str(lead.id), "status": lead.status, "already_existed": False}


async def create_appointment_intent(
    ctx: ToolContext, *, preferred_time: str | None = None, **_: Any
) -> dict:
    if ctx.lead is None:
        raise ToolError("No lead on this conversation yet — call create_lead first.")
    if preferred_time:
        await leads_repo.update_lead(ctx.db, ctx.lead, {"preferred_time": preferred_time})
    updated = await leads_service.transition_lead_status(ctx.db, ctx.lead, "APPOINTMENT_INTENT")
    return {"lead_id": str(updated.id), "status": updated.status}


async def check_appointment_availability(ctx: ToolContext, **_: Any) -> dict:
    # Honest stub — CLAUDE.md §25's exact prescribed pattern for calendar
    # unavailable. Phase 7 (CalendarProvider) replaces this with real slots.
    return {
        "available": None,
        "message": (
            "Live availability isn't connected yet. The clinic will confirm the exact time "
            "directly — I'll flag this for them now."
        ),
    }


async def book_appointment(ctx: ToolContext, **_: Any) -> dict:
    # Never marks an appointment "booked" without a real calendar
    # confirmation (CLAUDE.md §15/§18) — escalates instead of fabricating.
    if ctx.lead is not None:
        await leads_service.transition_lead_status(ctx.db, ctx.lead, "HUMAN_REQUIRED")
    return {
        "booked": False,
        "message": (
            "I can't confirm live booking yet — a member of the clinic team will reach out "
            "to lock in the exact time."
        ),
    }


async def reschedule_appointment(ctx: ToolContext, **_: Any) -> dict:
    if ctx.lead is not None:
        await leads_service.transition_lead_status(ctx.db, ctx.lead, "HUMAN_REQUIRED")
    return {
        "rescheduled": False,
        "message": "I can't reschedule automatically yet — the clinic will confirm a new time.",
    }


async def cancel_appointment(ctx: ToolContext, **_: Any) -> dict:
    if ctx.lead is None:
        raise ToolError("No lead on this conversation — nothing to cancel.")
    appointments = await appointments_repo.list_appointments(
        ctx.db, ctx.clinic_id, lead_id=ctx.lead.id
    )
    active = [a for a in appointments if a.status not in ("cancelled", "completed", "no_show")]
    if not active:
        return {"cancelled": False, "message": "No active appointment found to cancel."}
    appointment = active[0]
    await transition_appointment_status(ctx.db, appointment, "cancelled", ctx.lead)
    return {"cancelled": True, "appointment_id": str(appointment.id)}


async def get_appointment_status(ctx: ToolContext, **_: Any) -> dict:
    if ctx.lead is None:
        raise ToolError("No lead on this conversation — nothing to look up.")
    appointments = await appointments_repo.list_appointments(
        ctx.db, ctx.clinic_id, lead_id=ctx.lead.id
    )
    if not appointments:
        return {"appointments": []}
    return {
        "appointments": [
            {
                "status": a.status,
                "start": a.start.isoformat() if a.start else None,
                "location": a.location,
            }
            for a in appointments
        ]
    }


async def escalate_to_human(ctx: ToolContext, *, reason: str, **_: Any) -> dict:
    if ctx.lead is None:
        raise ToolError("No lead on this conversation to escalate.")
    await leads_service.transition_lead_status(ctx.db, ctx.lead, "HUMAN_REQUIRED")
    return {"escalated": True, "reason": reason}


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_clinic_details",
            "description": "Get the clinic's name, contact info, locations, and opening hours.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_treatment_details",
            "description": "Get approved overview info for a specific treatment by name.",
            "parameters": {
                "type": "object",
                "properties": {"treatment_name": {"type": "string"}},
                "required": ["treatment_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_clinic_knowledge",
            "description": (
                "Search the clinic's approved knowledge base (FAQs, policies, treatment info, "
                "and doctor profiles/specialties). Use this for open-ended questions the other "
                "tools don't directly cover — including 'which doctor does X' or 'who performs "
                "X' when you don't already have a specific doctor's name to look up."
            ),
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_doctor_details",
            "description": (
                "Get a specific doctor's title, specialties, credentials, and bio — only when "
                "you already know their name. If you don't have a name yet (e.g. 'which doctor "
                "treats veneers'), use search_clinic_knowledge instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {"doctor_name": {"type": "string"}},
                "required": ["doctor_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_approved_price_guidance",
            "description": "Get approved price guidance for a specific treatment by name.",
            "parameters": {
                "type": "object",
                "properties": {"treatment_name": {"type": "string"}},
                "required": ["treatment_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_booking_policies",
            "description": "Get the clinic's approved booking/cancellation policy documents.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_lead",
            "description": (
                "Create a CRM lead for this visitor once you have their name, phone, and "
                "explicit consent to be contacted. Only call once per conversation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "phone": {"type": "string"},
                    "treatment_name": {"type": "string"},
                    "preferred_time": {"type": "string"},
                    "consent": {
                        "type": "boolean",
                        "description": (
                            "True only if the visitor explicitly agreed to be contacted."
                        ),
                    },
                },
                "required": ["name", "phone", "consent"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_appointment_intent",
            "description": (
                "Record that the visitor wants to book an appointment, with their preferred "
                "time. Requires a lead to already exist."
            ),
            "parameters": {
                "type": "object",
                "properties": {"preferred_time": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_appointment_availability",
            "description": "Check live appointment availability for a treatment/time.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book an appointment at a confirmed available time.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_appointment",
            "description": "Reschedule the visitor's existing appointment to a new time.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel the visitor's existing appointment.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_appointment_status",
            "description": "Look up the status of the visitor's existing appointment(s).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": (
                "Hand this conversation off to clinic staff — use whenever the visitor asks "
                "for a human, asks something clinical/medical, an emergency comes up, or you "
                "are not confident in an approved answer."
            ),
            "parameters": {
                "type": "object",
                "properties": {"reason": {"type": "string"}},
                "required": ["reason"],
            },
        },
    },
]

ToolHandler = Callable[..., Awaitable[dict]]

TOOL_HANDLERS: dict[str, ToolHandler] = {
    "get_clinic_details": get_clinic_details,
    "get_treatment_details": get_treatment_details,
    "search_clinic_knowledge": search_clinic_knowledge,
    "get_doctor_details": get_doctor_details,
    "get_approved_price_guidance": get_approved_price_guidance,
    "get_booking_policies": get_booking_policies,
    "create_lead": create_lead,
    "create_appointment_intent": create_appointment_intent,
    "check_appointment_availability": check_appointment_availability,
    "book_appointment": book_appointment,
    "reschedule_appointment": reschedule_appointment,
    "cancel_appointment": cancel_appointment,
    "get_appointment_status": get_appointment_status,
    "escalate_to_human": escalate_to_human,
}
