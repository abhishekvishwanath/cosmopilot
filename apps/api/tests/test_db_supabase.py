from typing import Any

import pytest

from app.core.config import Settings
from app.db.supabase import check_supabase_connection


class _FakeResponse:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse):
        self._response = response
        self.last_headers: dict[str, str] | None = None

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        return None

    async def get(self, url: str, headers: dict[str, str]) -> _FakeResponse:
        self.last_headers = headers
        return self._response


def _settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "supabase_url": "https://example.supabase.co",
        "supabase_anon_key": "anon-key",
    }
    base.update(overrides)
    return Settings(**base)


async def test_not_configured_without_url() -> None:
    settings = Settings(supabase_url=None, supabase_anon_key=None)
    result = await check_supabase_connection(settings)
    assert result.status == "not_configured"


async def test_ok_when_service_role_key_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _FakeAsyncClient(_FakeResponse(200))
    monkeypatch.setattr(
        "app.db.supabase.httpx.AsyncClient", lambda **_: fake_client
    )
    settings = _settings(supabase_service_role_key="service-role-key")

    result = await check_supabase_connection(settings)

    assert result.status == "ok"
    assert fake_client.last_headers is not None
    assert fake_client.last_headers["apikey"] == "service-role-key"


async def test_anon_only_rejected_at_introspection_is_still_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = _FakeAsyncClient(
        _FakeResponse(
            401,
            '{"message":"Invalid API key","hint":"Only the `service_role` API key '
            'can be used for this endpoint."}',
        )
    )
    monkeypatch.setattr(
        "app.db.supabase.httpx.AsyncClient", lambda **_: fake_client
    )
    settings = _settings()  # anon key only, no service role key

    result = await check_supabase_connection(settings)

    assert result.status == "ok"
    assert result.detail is not None and "SUPABASE_SERVICE_ROLE_KEY" in result.detail


async def test_genuinely_bad_key_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _FakeAsyncClient(
        _FakeResponse(401, '{"message":"Invalid authentication credentials"}')
    )
    monkeypatch.setattr(
        "app.db.supabase.httpx.AsyncClient", lambda **_: fake_client
    )
    settings = _settings()

    result = await check_supabase_connection(settings)

    assert result.status == "error"
    assert result.detail is not None and "SUPABASE_ANON_KEY" in result.detail
