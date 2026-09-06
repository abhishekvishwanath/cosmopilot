import uuid
from typing import Any

import httpx

from app.providers.llm.base import ChatMessage, ChatResponse, LLMProvider, LLMResponse, ToolCall


class OllamaError(RuntimeError):
    """Ollama unreachable or returned something unusable — never silently
    treated as success (CLAUDE.md §25); the caller decides the fallback."""


class OllamaLLMProvider(LLMProvider):
    """Free, local, no-API-key generation via a locally running Ollama
    daemon — project decision to use llama3 for the prototype."""

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def generate(self, *, system: str, context: str, question: str) -> LLMResponse:
        prompt = f"Context (the ONLY information you may use):\n{context}\n\nQuestion: {question}"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self._base_url}/api/generate",
                    json={
                        "model": self._model,
                        "system": system,
                        "prompt": prompt,
                        "stream": False,
                        # Grounded QA wants consistent, repeatable answers
                        # from the same context, not creative variation —
                        # temperature=0 removes sampling randomness so the
                        # same question doesn't sometimes refuse and
                        # sometimes answer from identical retrieved chunks.
                        "options": {"temperature": 0},
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama request failed: {exc}") from exc

        text = str(response.json().get("response", "")).strip()
        if not text:
            raise OllamaError("Ollama returned an empty response.")
        return LLMResponse(text=text, model=self._model)

    async def chat(
        self, *, messages: list[ChatMessage], tools: list[dict[str, Any]] | None = None
    ) -> ChatResponse:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": list(messages),
            "stream": False,
            "options": {"temperature": 0},
        }
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(f"{self._base_url}/api/chat", json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama chat request failed: {exc}") from exc

        message = response.json().get("message", {})
        content = message.get("content") or None
        tool_calls = [
            ToolCall(
                id=str(call.get("id") or uuid.uuid4()),
                name=call["function"]["name"],
                arguments=call["function"].get("arguments", {}),
            )
            for call in message.get("tool_calls", []) or []
        ]
        if content is None and not tool_calls:
            raise OllamaError("Ollama returned neither content nor a tool call.")
        return ChatResponse(content=content, model=self._model, tool_calls=tool_calls)
