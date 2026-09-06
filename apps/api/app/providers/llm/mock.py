from typing import Any

from app.providers.llm.base import ChatMessage, ChatResponse, LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """
    No real generation — returns the retrieved context verbatim (for
    generate()) or a static, honest non-answer (for chat()) so the demo
    still works when Ollama isn't installed or running, without ever
    inventing text (CLAUDE.md §25 — never fabricate a successful action).
    Never issues tool calls — it has no reasoning behind it to decide
    when one is warranted.
    """

    async def generate(self, *, system: str, context: str, question: str) -> LLMResponse:
        text = context.strip() or "I don't have approved information to answer that yet."
        return LLMResponse(text=text, model="mock")

    async def chat(
        self, *, messages: list[ChatMessage], tools: list[dict[str, Any]] | None = None
    ) -> ChatResponse:
        return ChatResponse(
            content="The AI concierge isn't connected right now — please use the enquiry form "
            "or WhatsApp and the clinic will follow up directly.",
            model="mock",
        )
