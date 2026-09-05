import uuid

from app.providers.email import get_email_provider
from app.providers.email.mock import MockEmailProvider


async def test_mock_email_provider_reports_sent() -> None:
    provider = MockEmailProvider()
    handle = await provider.send(
        to="clinic@example.com",
        subject="New enquiry",
        body="Jane Doe enquired about Veneers.",
        clinic_id=uuid.uuid4(),
    )
    assert handle.sent is True
    assert handle.provider == "mock"
    assert handle.to == "clinic@example.com"


def test_get_email_provider_returns_mock_by_default() -> None:
    assert isinstance(get_email_provider(), MockEmailProvider)
