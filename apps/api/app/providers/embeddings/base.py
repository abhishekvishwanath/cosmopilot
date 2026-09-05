from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    dimensions: int

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Returns one embedding vector per input text, same order."""
        ...
