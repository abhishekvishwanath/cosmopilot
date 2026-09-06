from app.providers.llm.mock import MockLLMProvider


async def test_mock_llm_chat_returns_no_tool_calls() -> None:
    provider = MockLLMProvider()
    response = await provider.chat(messages=[{"role": "user", "content": "Hi"}])
    assert response.tool_calls == []
    assert response.content is not None
    assert "form" in response.content or "WhatsApp" in response.content


async def test_mock_llm_chat_ignores_tools_argument() -> None:
    provider = MockLLMProvider()
    response = await provider.chat(
        messages=[{"role": "user", "content": "Hi"}],
        tools=[{"type": "function", "function": {"name": "noop", "parameters": {}}}],
    )
    assert response.tool_calls == []
