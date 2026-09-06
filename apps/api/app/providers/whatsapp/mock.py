import logging
import uuid

from app.core.logging import log_with_fields
from app.providers.whatsapp.base import MessageHandle, WhatsAppProvider

logger = logging.getLogger("cosmopilot.providers.whatsapp")


class MockWhatsAppProvider(WhatsAppProvider):
    """Logs the would-be WhatsApp message instead of calling the Meta Cloud
    API (CLAUDE.md §26). The caller is responsible for persisting it as a
    Message row on the lead's conversation — this provider only reports
    whether the "send" itself succeeded, same division of responsibility
    as MockEmailProvider."""

    async def send_message(self, *, to: str, text: str) -> MessageHandle:
        log_with_fields(logger, logging.INFO, "mock_whatsapp_send", to=to)
        return MessageHandle(
            provider="mock",
            to=to,
            sent=True,
            external_id=uuid.uuid4().hex,
            detail="MOCK_MODE — logged only, no real WhatsApp message sent.",
        )
