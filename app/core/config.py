"""Environment-based application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Secure AI Platform API"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # SecretStr prevents accidental plaintext exposure in repr/debug output.
    viewer_api_key: SecretStr = Field(min_length=16)
    analyst_api_key: SecretStr = Field(min_length=16)
    admin_api_key: SecretStr = Field(min_length=16)


@lru_cache
def get_settings() -> Settings:
    """Load and cache validated application settings."""
    return Settings()  # type: ignore[call-arg]

