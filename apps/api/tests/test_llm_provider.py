from app.providers.llm.mock import MockLLMProvider


async def test_mock_llm_returns_context_verbatim() -> None:
    provider = MockLLMProvider()
    response = await provider.generate(
        system="Answer only from context.",
        context="Veneers typically last 10-15 years.",
        question="How long do veneers last?",
    )
    assert response.text == "Veneers typically last 10-15 years."
    assert response.model == "mock"


async def test_mock_llm_refuses_with_no_context() -> None:
    provider = MockLLMProvider()
    response = await provider.generate(system="", context="", question="What's the weather?")
    assert "don't have approved information" in response.text
