"""
Outbound event dispatch to n8n (CLAUDE.md §6/§13/§17, Phase 8). FastAPI
stays the source of truth for state — this only *notifies* n8n that
something happened so its workflows can react (send a WhatsApp follow-up,
notify the clinic, etc). Never awaited for its result to decide anything:
n8n being unreachable or unconfigured must never block or fail the request
that triggered the notification (CLAUDE.md §25).
"""

import logging
import uuid
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import log_with_fields

logger = logging.getLogger("cosmopilot.services.n8n")


async def notify_n8n(event_type: str, payload: dict[str, Any]) -> None:
    settings = get_settings()
    if not settings.n8n_webhook_base_url:
        return  # not configured — the rest of the demo works without it

    url = f"{settings.n8n_webhook_base_url.rstrip('/')}/webhook/{event_type}"
    headers = {}
    if settings.n8n_webhook_shared_secret:
        headers["X-Webhook-Secret"] = settings.n8n_webhook_shared_secret

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        log_with_fields(
            logger,
            logging.WARNING,
            "n8n_dispatch_failed",
            event_type=event_type,
            error=str(exc),
        )


async def notify_lead_created(lead_id: uuid.UUID, clinic_id: uuid.UUID) -> None:
    await notify_n8n("lead.created", {"lead_id": str(lead_id), "clinic_id": str(clinic_id)})


async def notify_call_unanswered(lead_id: uuid.UUID, clinic_id: uuid.UUID) -> None:
    # Phase 10: with a real (async) VoiceProvider, the call's outcome is
    # only known once Vapi's end-of-call-report webhook arrives — that
    # handler is what decides "unanswered" and calls this directly, rather
    # than n8n's Workflow A branching on a synchronous field the way it did
    # against the Phase 8 mock (see workflows/n8n/workflow-a-new-lead.json).
    await notify_n8n("call.unanswered", {"lead_id": str(lead_id), "clinic_id": str(clinic_id)})


async def notify_appointment_status_changed(
    *,
    appointment_id: uuid.UUID,
    lead_id: uuid.UUID,
    clinic_id: uuid.UUID,
    from_status: str,
    to_status: str,
) -> None:
    await notify_n8n(
        "appointment.status_changed",
        {
            "appointment_id": str(appointment_id),
            "lead_id": str(lead_id),
            "clinic_id": str(clinic_id),
            "from_status": from_status,
            "to_status": to_status,
        },
    )
