import asyncio
import json
import uuid
from typing import Any

import httpx

from app.providers.llm.base import (
    ChatMessage,
    ChatResponse,
    LLMProvider,
    LLMProviderError,
    LLMResponse,
    ToolCall,
)

_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# The free/on-demand tier's tokens-per-minute cap is a fast-refilling burst
# limiter (observed live: resets in single-digit seconds, not a full
# minute), not a hard quota — a real visitor typing at human speed won't
# hit it, but back-to-back turns (or two concurrent visitors) can. One
# short retry absorbs that without ever surfacing a 429 as a broken
# conversation (CLAUDE.md §25 — "safe retries" for rate limits).
_MAX_RETRIES_ON_RATE_LIMIT = 1
_DEFAULT_RETRY_SECONDS = 3.0


class GroqError(LLMProviderError):
    """Groq unreachable, unauthorized, or returned something unusable —
    never silently treated as success (CLAUDE.md §25); the caller decides
    the fallback."""


class GroqLLMProvider(LLMProvider):
    """
    Hosted inference via Groq's OpenAI-compatible API — project decision
    (2026-09-06) to move off local Ollama after observed hallucination and
    unreliable tool-calling with qwen2.5:7b on-device. `openai/gpt-oss-120b`
    is Groq's largest open-weight (Apache-2.0) model with tool-calling
    support, chosen over the smaller gpt-oss-20b and qwen3.x options
    available on this account for the strongest reasoning/tool-selection
    reliability the concierge's safety guarantees (CLAUDE.md §5.3/§25) lean
    on. Requires GROQ_API_KEY — no local daemon, no GPU/RAM footprint.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def _complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(_MAX_RETRIES_ON_RATE_LIMIT + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        _API_URL,
                        headers={"Authorization": f"Bearer {self._api_key}"},
                        json=payload,
                    )
                    response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and attempt < _MAX_RETRIES_ON_RATE_LIMIT:
                    retry_after = exc.response.headers.get("retry-after")
                    delay = float(retry_after) if retry_after else _DEFAULT_RETRY_SECONDS
                    await asyncio.sleep(delay)
                    continue
                raise GroqError(
                    f"Groq request failed: {exc.response.status_code} {exc.response.text}"
                ) from exc
            except httpx.HTTPError as exc:
                raise GroqError(f"Groq request failed: {exc}") from exc
            return response.json()
        raise AssertionError("unreachable")  # loop always returns or raises

    async def generate(self, *, system: str, context: str, question: str) -> LLMResponse:
        prompt = f"Context (the ONLY information you may use):\n{context}\n\nQuestion: {question}"
        body = await self._complete(
            {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                # Grounded QA wants consistent, repeatable answers from the
                # same context, not creative variation.
                "temperature": 0,
            }
        )
        text = str(body["choices"][0]["message"].get("content") or "").strip()
        if not text:
            raise GroqError("Groq returned an empty response.")
        return LLMResponse(text=text, model=self._model)

    async def chat(
        self, *, messages: list[ChatMessage], tools: list[dict[str, Any]] | None = None
    ) -> ChatResponse:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": list(messages),
            "temperature": 0,
        }
        if tools:
            payload["tools"] = tools

        body = await self._complete(payload)
        message = body["choices"][0]["message"]
        content = message.get("content") or None

        tool_calls: list[ToolCall] = []
        for call in message.get("tool_calls", []) or []:
            function = call["function"]
            raw_arguments = function.get("arguments") or "{}"
            try:
                # Groq's Chat Completions API (like OpenAI's) sends
                # `arguments` as a JSON-encoded string, not a parsed
                # object — Ollama's own /api/chat sends it pre-parsed,
                # which is the one shape difference this provider needs to
                # bridge for the rest of the app's ToolCall type to stay
                # provider-agnostic.
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError as exc:
                raise GroqError(f"Groq tool call had unparseable arguments: {exc}") from exc
            tool_calls.append(
                ToolCall(
                    id=str(call.get("id") or uuid.uuid4()),
                    name=function["name"],
                    arguments=arguments,
                )
            )

        if content is None and not tool_calls:
            raise GroqError("Groq returned neither content nor a tool call.")
        return ChatResponse(content=content, model=self._model, tool_calls=tool_calls)
