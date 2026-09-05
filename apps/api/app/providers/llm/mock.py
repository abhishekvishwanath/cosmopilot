from app.providers.llm.base import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """
    No real generation — returns the retrieved context verbatim so the
    demo still shows something grounded when Ollama isn't installed or
    running, without ever inventing text (CLAUDE.md §25 — never fabricate
    a successful action).
    """

    async def generate(self, *, system: str, context: str, question: str) -> LLMResponse:
        text = context.strip() or "I don't have approved information to answer that yet."
        return LLMResponse(text=text, model="mock")
