from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Project configuration loaded from
    environment variables (and .env file).

    Priority (typical):
    1) OS environment variables
    2) .env file (local dev)
    3) defaults below
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Example settings (edit to your needs)
    log_level: str = Field(
        default="INFO",
        description="Logging level, e.g. DEBUG/INFO/WARNING",
    )
    db_url: str = Field(
        default="sqlite:///./local.db",
        description="Database connection string",
    )
    run_env: str = Field(default="local", description="local/dev/stage/prod")
    random_seed: int = Field(default=42, description="Global random seed")


settings = Settings()
