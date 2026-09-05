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
        return bool(self.supabase_jwt_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
