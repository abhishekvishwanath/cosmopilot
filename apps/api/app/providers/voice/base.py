from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

# "initiated" is what a real, asynchronous provider (Vapi, Phase 10) would
# return immediately — the eventual outcome arrives later via that
# provider's own webhook, never fabricated here. A synchronous mock can
# resolve straight to "answered"/"no_answer" since there's no real call in
# flight to wait on.
CallStatus = Literal["initiated", "answered", "no_answer", "failed"]


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
    async def start_call(self, *, to: str, clinic_name: str, lead_name: str) -> CallHandle: ...
