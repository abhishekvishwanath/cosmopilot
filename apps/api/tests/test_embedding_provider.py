from app.providers.embeddings.mock import MockEmbeddingProvider


async def test_mock_embedding_is_deterministic() -> None:
    provider = MockEmbeddingProvider()
    a = await provider.embed(["Porcelain veneers last 10-15 years."])
    b = await provider.embed(["Porcelain veneers last 10-15 years."])
    assert a == b


async def test_mock_embedding_has_correct_dimensions() -> None:
    provider = MockEmbeddingProvider()
    [vector] = await provider.embed(["Invisalign takes 6-18 months."])
    assert len(vector) == provider.dimensions == 384


async def test_mock_embedding_is_unit_normalized() -> None:
    provider = MockEmbeddingProvider()
    [vector] = await provider.embed(["Dental implants."])
    norm = sum(v * v for v in vector) ** 0.5
    assert abs(norm - 1.0) < 1e-6


async def test_mock_embedding_batches_preserve_order() -> None:
    provider = MockEmbeddingProvider()
    texts = ["veneers", "implants", "whitening"]
    vectors = await provider.embed(texts)
    individually = [(await provider.embed([t]))[0] for t in texts]
    assert vectors == individually
