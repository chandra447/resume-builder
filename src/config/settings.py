from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # API Keys
    firecrawl_api_key: Optional[str] = Field(
        validation_alias="FIRECRAWL_API_KEY", default=None
    )
    openai_api_key: Optional[str] = Field(
        validation_alias="OPENAI_API_KEY", default=None
    )
    PROJECT_NAME: str = "Resume Tailoring"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    api_reload: bool = True

    # Model Configuration
    model_name: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 4000
    backend_cors_origins: list = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


# Create a global settings instance
settings = Settings()
