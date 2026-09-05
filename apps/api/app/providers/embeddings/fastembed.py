import asyncio
from typing import Any

from app.providers.embeddings.base import EmbeddingProvider

MODEL_NAME = "BAAI/bge-small-en-v1.5"


class FastEmbedProvider(EmbeddingProvider):
    """
    Free, local, no-API-key embeddings via fastembed (ONNX runtime) —
    project decision to use bge-small-en-v1.5 for the prototype, with
    upgrading to a paid provider (OpenAI/Voyage) purely a config change
    later, since callers only depend on EmbeddingProvider.embed().
    """

    dimensions = 384

    def __init__(self) -> None:
        self._model: Any = None

    def _get_model(self) -> Any:
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=MODEL_NAME)
        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # fastembed is synchronous, CPU-bound ONNX inference — offload so it
        # doesn't block the event loop other requests are running on.
        return await asyncio.to_thread(self._embed_sync, texts)

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        return [vector.tolist() for vector in model.embed(texts)]
