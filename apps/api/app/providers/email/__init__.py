from functools import lru_cache

from app.providers.email.base import EmailProvider
from app.providers.email.mock import MockEmailProvider

__all__ = ["EmailProvider", "get_email_provider"]


@lru_cache
def get_email_provider() -> EmailProvider:
    # No Resend adapter yet — nothing in Phase 4 needs it, and CLAUDE.md's
    # credential protocol (§32) says don't request a key before a phase
    # actually needs it. Swap this for a ResendEmailProvider (reading
    # RESEND_API_KEY from Settings) once real sending is required — no
    # caller of get_email_provider() needs to change.
    return MockEmailProvider()
