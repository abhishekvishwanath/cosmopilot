import httpx

from app.providers.llm.base import LLMProvider, LLMResponse


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
