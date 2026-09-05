from functools import lru_cache

from app.core.config import get_settings
from app.providers.embeddings.base import EmbeddingProvider
from app.providers.embeddings.mock import MockEmbeddingProvider

__all__ = ["EmbeddingProvider", "get_embedding_provider"]


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider == "fastembed":
        from app.providers.embeddings.fastembed import FastEmbedProvider

        return FastEmbedProvider()
    return MockEmbeddingProvider()
