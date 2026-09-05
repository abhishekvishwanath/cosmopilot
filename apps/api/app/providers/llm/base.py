from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, *, system: str, context: str, question: str) -> LLMResponse:
        """
        `context` is the retrieved, approved knowledge the answer must be
        grounded in; `question` is the visitor's question. Kept as
        separate structural fields — not one merged prompt string — so
        grounding is enforced by every implementation (including
        MockLLMProvider), not just by prompt-writing convention.
        """
        ...
