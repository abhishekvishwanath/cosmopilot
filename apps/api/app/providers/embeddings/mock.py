import hashlib
import random

from app.providers.embeddings.base import EmbeddingProvider


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic, dependency-free embeddings for tests/CI — same text
    always produces the same vector, unrelated texts produce effectively
    unrelated vectors, but there's no real semantic understanding behind
    it. Never use for anything a retrieval-quality judgment depends on.
    """

    dimensions = 384

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)
        raw = [rng.gauss(0, 1) for _ in range(self.dimensions)]
        norm = sum(v * v for v in raw) ** 0.5 or 1.0
        return [v / norm for v in raw]
