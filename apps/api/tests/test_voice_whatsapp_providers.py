from app.providers.voice.mock import MockVoiceProvider
from app.providers.whatsapp.mock import MockWhatsAppProvider


async def test_mock_voice_provider_alternates_answered_and_no_answer() -> None:
    """
    CLAUDE.md §26's own suggestion for the voice mock ("deterministically
    alternating answered/no-answer") — reproducible, not random, so the two
    demo scenarios in CLAUDE.md §36 (successful call, missed call) are each
    reachable on demand rather than by luck.
    """
    provider = MockVoiceProvider()
    first = await provider.start_call(to="+971500000000", clinic_name="Cosmo Dental", lead_name="A")
    second = await provider.start_call(
        to="+971500000000", clinic_name="Cosmo Dental", lead_name="B"
    )
    third = await provider.start_call(to="+971500000000", clinic_name="Cosmo Dental", lead_name="C")

    assert first.status == "answered"
    assert second.status == "no_answer"
    assert third.status == "answered"
    assert first.call_id != second.call_id


async def test_mock_whatsapp_provider_reports_sent() -> None:
    provider = MockWhatsAppProvider()
    handle = await provider.send_message(to="+971500000000", text="Hello")

    assert handle.sent is True
    assert handle.provider == "mock"
    assert handle.external_id is not None
