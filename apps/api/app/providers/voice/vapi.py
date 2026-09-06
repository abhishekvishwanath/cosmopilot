"""
Real outbound calling via Vapi (Phase 10). Vapi is call transport only
(CLAUDE.md §7) — the assistant it runs (model, tools, system prompt) is
provisioned once by scripts/create_vapi_assistant.py from the exact same
sources the text Concierge uses, so this adapter's only job is starting
the call and returning immediately.

Unlike MockVoiceProvider, a real call's outcome isn't known synchronously
— it arrives later via Vapi's own end-of-call-report webhook (see
app/api/v1/vapi.py), which is what actually transitions the lead to
CONTACTED/NO_ANSWER (CLAUDE.md §25 — never fabricate an outcome that
hasn't happened yet).
"""

import logging
import uuid
from typing import Any

import httpx

from app.core.logging import log_with_fields
from app.providers.voice.base import CallHandle, VoiceProvider, VoiceProviderError

logger = logging.getLogger("cosmopilot.providers.voice.vapi")

_API_URL = "https://api.vapi.ai/call"


class VapiError(VoiceProviderError):
    """Vapi's API rejected or failed the outbound call request."""


class VapiVoiceProvider(VoiceProvider):
    def __init__(
        self, *, api_key: str, assistant_id: str, phone_number_id: str
    ) -> None:
        self._api_key = api_key
        self._assistant_id = assistant_id
        self._phone_number_id = phone_number_id

    async def start_call(
        self,
        *,
        to: str,
        clinic_name: str,
        lead_name: str,
        clinic_id: uuid.UUID | None = None,
        lead_id: uuid.UUID | None = None,
        treatment_name: str | None = None,
    ) -> CallHandle:
        treatment_context = f" about {treatment_name}" if treatment_name else ""
        payload: dict[str, Any] = {
            "assistantId": self._assistant_id,
            "phoneNumberId": self._phone_number_id,
            "customer": {"number": to, "name": lead_name},
            "assistantOverrides": {
                "variableValues": {
                    "lead_name": lead_name,
                    "clinic_name": clinic_name,
                    "treatment_context": treatment_context,
                },
                # Read back on every webhook for this call (tool-calls,
                # end-of-call-report) to correlate to our own lead/clinic —
                # never inferred from the phone number alone.
                "metadata": {
                    "lead_id": str(lead_id) if lead_id else None,
                    "clinic_id": str(clinic_id) if clinic_id else None,
                },
            },
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    _API_URL,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise VapiError(
                f"Vapi call request failed: {exc.response.status_code} {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise VapiError(f"Vapi call request failed: {exc}") from exc

        call = response.json()
        call_id = call.get("id", "")
        log_with_fields(
            logger,
            logging.INFO,
            "vapi_call_initiated",
            to=to,
            clinic_name=clinic_name,
            call_id=call_id,
        )
        # "initiated" is the only honest status here — the real outcome
        # arrives later via the webhook (see base.py's CallStatus doc).
        return CallHandle(call_id=call_id, status="initiated")
