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

    # AI knowledge base (Phase 5) — embeddings stay free/local
    # (bge-small-en-v1.5 via fastembed, no API key). The answer-generation
    # LLM moved off local Ollama on 2026-09-06 after live testing showed
    # qwen2.5:7b hallucinating and unreliably issuing tool calls in
    # multi-turn conversations (see the Phase 6/7 reports) — Groq's hosted
    # inference now serves both grounded QA and the AI Concierge's tool
    # calling. "mock" is available for tests/CI needing neither dependency.
    embedding_provider: Literal["fastembed", "mock"] = "fastembed"
    llm_provider: Literal["groq", "ollama", "mock"] = "groq"

    groq_api_key: str | None = None
    # openai/gpt-oss-120b — Groq's largest open-weight (Apache-2.0) model
    # with tool-calling support, chosen for the strongest tool-selection
    # reliability among the tool-calling-capable models on this account
    # (also considered: openai/gpt-oss-20b, qwen/qwen3.8-27b).
    groq_model: str = "openai/gpt-oss-120b"

    # Kept as an alternative free/local option (CLAUDE.md §5.6 — providers
    # must stay swappable) even though it's no longer the default.
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    # n8n automation (Phase 8) — n8n is the orchestration layer for
    # webhooks/delays/branching/notifications (CLAUDE.md §6); core
    # application state stays in FastAPI/Postgres. `n8n_webhook_base_url`
    # is where FastAPI pushes outbound events (lead.created,
    # appointment.status_changed) as n8n Webhook-trigger URLs; n8n's own
    # HTTP Request nodes call back into `/api/v1/webhooks/n8n/*`,
    # authenticated by `n8n_webhook_shared_secret` (a static shared secret
    # header — n8n's HTTP Request node doesn't do request signing the way
    # Meta/Stripe webhooks do, so this is the pragmatic equivalent CLAUDE.md
    # §24 asks for at this trust boundary). Both unset means n8n isn't
    # wired up yet — outbound dispatch is skipped, never blocking the
    # request it's attached to (CLAUDE.md §25).
    n8n_webhook_base_url: str | None = None
    n8n_webhook_shared_secret: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
