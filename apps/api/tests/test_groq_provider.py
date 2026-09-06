"""
Unit tests for GroqLLMProvider, mocking httpx the same way
test_db_supabase.py does — no real network call. These cover the one
shape difference from OllamaLLMProvider that matters for correctness:
Groq's OpenAI-compatible API sends tool call `arguments` as a JSON-encoded
string, not a pre-parsed object, so this provider must decode it before
handing a plain dict back to app/agents/tools.py (CLAUDE.md §27 — core
logic depends on the provider-agnostic ToolCall type, not any vendor's
wire format).
"""

import json
from typing import Any

import pytest

from app.providers.llm.groq import GroqError, GroqLLMProvider


class _FakeResponse:
    def __init__(self, status_code: int, body: dict[str, Any]):
        self.status_code = status_code
        self._body = body
        self.text = json.dumps(body)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError("error", request=None, response=self)  # type: ignore[arg-type]

    def json(self) -> dict[str, Any]:
        return self._body


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse):
        self._response = response
        self.last_json: dict[str, Any] | None = None

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        return None

    async def post(self, url: str, headers: dict[str, str], json: dict[str, Any]) -> _FakeResponse:
        self.last_json = json
        return self._response


def _chat_completion(message: dict[str, Any]) -> dict[str, Any]:
    return {"choices": [{"message": message}]}


async def test_generate_returns_text_content(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _FakeAsyncClient(
        _FakeResponse(
            200, _chat_completion({"role": "assistant", "content": "Veneers last 10-15 years."})
        )
    )
    monkeypatch.setattr("app.providers.llm.groq.httpx.AsyncClient", lambda **_: fake_client)

    provider = GroqLLMProvider(api_key="test-key", model="openai/gpt-oss-120b")
    response = await provider.generate(system="Be factual.", context="ctx", question="How long?")

    assert response.text == "Veneers last 10-15 years."
    assert response.model == "openai/gpt-oss-120b"


async def test_generate_raises_on_empty_content(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _FakeAsyncClient(
        _FakeResponse(200, _chat_completion({"role": "assistant", "content": ""}))
    )
    monkeypatch.setattr("app.providers.llm.groq.httpx.AsyncClient", lambda **_: fake_client)

    provider = GroqLLMProvider(api_key="test-key", model="openai/gpt-oss-120b")
    with pytest.raises(GroqError):
        await provider.generate(system="", context="", question="?")


async def test_chat_decodes_json_string_tool_call_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The exact shape Groq's API returns (verified live): `arguments` is a
    JSON string like '{"treatment_name": "veneers"}', not a dict.
    """
    fake_client = _FakeAsyncClient(
        _FakeResponse(
            200,
            _chat_completion(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "get_treatment_details",
                                "arguments": '{"treatment_name": "veneers"}',
                            },
                        }
                    ],
                }
            ),
        )
    )
    monkeypatch.setattr("app.providers.llm.groq.httpx.AsyncClient", lambda **_: fake_client)

    provider = GroqLLMProvider(api_key="test-key", model="openai/gpt-oss-120b")
    response = await provider.chat(messages=[{"role": "user", "content": "Tell me about veneers"}])

    assert response.content is None
    assert len(response.tool_calls) == 1
    call = response.tool_calls[0]
    assert call.id == "call_123"
    assert call.name == "get_treatment_details"
    assert call.arguments == {"treatment_name": "veneers"}


async def test_chat_handles_tool_call_with_no_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _FakeAsyncClient(
        _FakeResponse(
            200,
            _chat_completion(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "get_clinic_details"},
                        }
                    ],
                }
            ),
        )
    )
    monkeypatch.setattr("app.providers.llm.groq.httpx.AsyncClient", lambda **_: fake_client)

    provider = GroqLLMProvider(api_key="test-key", model="openai/gpt-oss-120b")
    response = await provider.chat(messages=[{"role": "user", "content": "hi"}])

    assert response.tool_calls[0].arguments == {}


async def test_chat_raises_on_malformed_tool_call_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = _FakeAsyncClient(
        _FakeResponse(
            200,
            _chat_completion(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "get_clinic_details",
                                "arguments": "{not valid json",
                            },
                        }
                    ],
                }
            ),
        )
    )
    monkeypatch.setattr("app.providers.llm.groq.httpx.AsyncClient", lambda **_: fake_client)

    provider = GroqLLMProvider(api_key="test-key", model="openai/gpt-oss-120b")
    with pytest.raises(GroqError):
        await provider.chat(messages=[{"role": "user", "content": "hi"}])


async def test_chat_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _FakeAsyncClient(_FakeResponse(401, {"error": "invalid api key"}))
    monkeypatch.setattr("app.providers.llm.groq.httpx.AsyncClient", lambda **_: fake_client)

    provider = GroqLLMProvider(api_key="bad-key", model="openai/gpt-oss-120b")
    with pytest.raises(GroqError):
        await provider.chat(messages=[{"role": "user", "content": "hi"}])
