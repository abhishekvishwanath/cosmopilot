from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict


class LLMProviderError(RuntimeError):
    """
    Base for provider-specific unavailable/failed-request errors (unreachable
    host, bad credentials, rate limit, malformed response). Callers (e.g.
    the concierge's turn loop) catch this one type to degrade gracefully
    regardless of which LLMProvider is configured (CLAUDE.md §5.6 provider
    abstraction, §25 never fabricate success on a failed call).
    """


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str


class ChatMessage(TypedDict, total=False):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: str  # only on role="tool" — which call this result answers
    name: str  # only on role="tool" — which tool produced it


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ChatResponse:
    content: str | None
    model: str
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, *, system: str, context: str, question: str) -> LLMResponse:
        """
        Single-shot grounded QA (Phase 5's knowledge base). `context` is the
        retrieved, approved knowledge the answer must be grounded in;
        `question` is the visitor's question. Kept as separate structural
        fields — not one merged prompt string — so grounding is enforced by
        every implementation (including MockLLMProvider), not just by
        prompt-writing convention.
        """
        ...

    @abstractmethod
    async def chat(
        self, *, messages: list[ChatMessage], tools: list[dict[str, Any]] | None = None
    ) -> ChatResponse:
        """
        Multi-turn conversation with optional tool calling (Phase 6's AI
        Concierge). `messages` follows the common role/content shape (plus
        tool_call_id/name for role="tool" results); `tools` is an OpenAI-
        style function-calling schema list — the shape Ollama's /api/chat
        and OpenAI's API both already accept, so it stays portable if the
        provider changes later.
        """
        ...
