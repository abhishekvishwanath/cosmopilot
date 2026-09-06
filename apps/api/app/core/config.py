from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration, loaded from environment variables / .env.

    Only Phase 1-relevant settings are declared here. Settings for later
    phases (AI provider, Vapi, WhatsApp, Stripe, n8n, ...) are added when
    that phase starts — see .env.example and docs/PROVIDER_INTERFACES.md.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "staging", "production"] = "development"
    log_level: str = "info"
    mock_mode: bool = True

    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"

    # Supabase — see README.md "Supabase setup from scratch" guide.
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_secret: str | None = None
    database_url: str | None = None

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key)

    @property
    def auth_configured(self) -> bool:
        # JWKS verification (asymmetric signing keys) needs only the project
        # URL; SUPABASE_JWT_SECRET is a fallback for projects still on the
        # legacy HS256 shared secret. Either is enough to attempt auth.
        return bool(self.supabase_url or self.supabase_jwt_secret)

    # AI knowledge base (Phase 5) — free/local by default per project
    # decision: bge-small-en-v1.5 via fastembed for embeddings, a local
    # Ollama model for grounded-answer generation. Both run with no API
    # key; "mock" is available for tests/CI where neither dependency is
    # installed or running.
    embedding_provider: Literal["fastembed", "mock"] = "fastembed"
    llm_provider: Literal["ollama", "mock"] = "ollama"
    ollama_url: str = "http://localhost:11434"
    # qwen2.5:7b, not llama3 — llama3 (Meta's original 3.0 release, already
    # on this machine) doesn't support tool calling at all in Ollama, which
    # Phase 6's AI Concierge needs. qwen2.5 also handles Phase 5's grounded
    # QA at least as well in testing, so one model now serves both.
    ollama_model: str = "qwen2.5:7b"


@lru_cache
def get_settings() -> Settings:
    return Settings()
