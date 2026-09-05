import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailHandle:
    """
    Structured result of a send attempt — services/ never touches a vendor's
    raw response shape (docs/PROVIDER_INTERFACES.md "design rules").
    """

    provider: str
    to: str
    subject: str
    sent: bool
    detail: str | None = None


class EmailProvider(ABC):
    @abstractmethod
    async def send(
        self, *, to: str, subject: str, body: str, clinic_id: uuid.UUID
    ) -> EmailHandle: ...
