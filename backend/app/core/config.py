"""
Central settings object. Everything the backend needs from the environment
comes through here — nothing reads os.environ directly elsewhere, so a
missing/misnamed env var fails fast and in one place.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    api_port: int = 8000
    allowed_origins: str = "http://localhost:3000"

    # Supabase — service role key never reaches the frontend.
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
