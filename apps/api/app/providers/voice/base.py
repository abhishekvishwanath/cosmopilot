import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

# "initiated" is what a real, asynchronous provider (Vapi, Phase 10) would
# return immediately — the eventual outcome arrives later via that
# provider's own webhook, never fabricated here. A synchronous mock can
# resolve straight to "answered"/"no_answer" since there's no real call in
# flight to wait on.
CallStatus = Literal["initiated", "answered", "no_answer", "failed"]


class VoiceProviderError(RuntimeError):
    """A real provider (Vapi) rejected or failed the call request itself —
    distinct from a normal call outcome (no_answer), this means the call
    never happened at all (bad number, provider/account limitation, etc).
    Callers must handle this gracefully (CLAUDE.md §25), never let it
    surface as an unhandled 500."""


@dataclass(frozen=True)
class CallHandle:
    """
    Structured result of an outbound call attempt — never a transcript or a
    booking decision (CLAUDE.md §9/§15: workflow state is never derived
    from free-form text, and the AI must never independently mark an
    appointment booked). `status` is the only thing n8n's call-answered /
    call-unanswered workflows branch on (docs/PROVIDER_INTERFACES.md's
    `VoiceProvider` contract).
    """

    call_id: str
    status: CallStatus


class VoiceProvider(ABC):
    @abstractmethod
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
        """
        `clinic_id`/`lead_id` let a real, asynchronous provider (Vapi) echo
        them back on its own webhooks to correlate an outcome to the right
        lead later — MockVoiceProvider ignores them since it never needs
        that round trip. `treatment_name` personalizes the call opener.
        """
        ...
