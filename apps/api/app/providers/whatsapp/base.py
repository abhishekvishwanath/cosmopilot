from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class MessageHandle:
    """Structured result of a send attempt — services/ never touches a
    vendor's raw response shape (docs/PROVIDER_INTERFACES.md design rules)."""

    provider: str
    to: str
    sent: bool
    external_id: str | None
    detail: str | None = None


class WhatsAppProvider(ABC):
    @abstractmethod
    async def send_message(self, *, to: str, text: str) -> MessageHandle: ...
