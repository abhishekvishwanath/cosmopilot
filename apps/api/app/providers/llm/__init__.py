from functools import lru_cache

from app.core.config import get_settings
from app.providers.llm.base import LLMProvider
from app.providers.llm.mock import MockLLMProvider

__all__ = ["LLMProvider", "get_llm_provider"]


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "groq":
        from app.providers.llm.groq import GroqLLMProvider

        if not settings.groq_api_key:
            raise RuntimeError("LLM_PROVIDER=groq requires GROQ_API_KEY to be set.")
        return GroqLLMProvider(api_key=settings.groq_api_key, model=settings.groq_model)
    if settings.llm_provider == "ollama":
        from app.providers.llm.ollama import OllamaLLMProvider

        return OllamaLLMProvider(base_url=settings.ollama_url, model=settings.ollama_model)
    return MockLLMProvider()
