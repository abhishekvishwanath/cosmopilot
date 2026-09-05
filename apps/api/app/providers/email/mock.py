import logging
import uuid

from app.core.logging import log_with_fields
from app.providers.email.base import EmailHandle, EmailProvider

logger = logging.getLogger("cosmopilot.providers.email")


class MockEmailProvider(EmailProvider):
    """Logs the would-be email instead of calling Resend (CLAUDE.md §26)."""

    async def send(
        self, *, to: str, subject: str, body: str, clinic_id: uuid.UUID
    ) -> EmailHandle:
        log_with_fields(
            logger,
            logging.INFO,
            "mock_email_send",
            to=to,
            subject=subject,
            clinic_id=str(clinic_id),
        )
        return EmailHandle(
            provider="mock",
            to=to,
            subject=subject,
            sent=True,
            detail="MOCK_MODE — logged only, no real email sent.",
        )
