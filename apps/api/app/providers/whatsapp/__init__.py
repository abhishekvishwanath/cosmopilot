from functools import lru_cache

from app.providers.whatsapp.base import MessageHandle, WhatsAppProvider
from app.providers.whatsapp.mock import MockWhatsAppProvider

__all__ = ["MessageHandle", "WhatsAppProvider", "get_whatsapp_provider"]


@lru_cache
def get_whatsapp_provider() -> WhatsAppProvider:
    # No Meta Cloud API adapter yet — needed starting Phase 9, once a
    # WhatsApp Business phone number/access token exists (CLAUDE.md §32).
    # Swap this for a MetaWhatsAppProvider then; no caller changes.
    return MockWhatsAppProvider()
