"""Application settings management."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, DirectoryPath, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized runtime configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    app_env: str = Field("local", validation_alias="APP_ENV")
    api_host: str = Field("0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(8000, validation_alias="API_PORT")

    database_url: str = Field(..., validation_alias="DATABASE_URL")
    redis_url: str = Field(..., validation_alias="REDIS_URL")

    llm_provider: Literal["openai", "transformers"] = Field(
        "transformers", validation_alias="LLM_PROVIDER"
    )
    embed_provider: Literal["openai", "transformers"] = Field(
        "transformers", validation_alias="EMBED_PROVIDER"
    )

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_llm_model: str = Field("gpt-4.1-mini", validation_alias="OPENAI_LLM_MODEL")
    openai_embed_model: str = Field("text-embedding-3-large", validation_alias="OPENAI_EMBED_MODEL")

    transformer_llm_model: str = Field(
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
        validation_alias="TRANSFORMER_LLM_MODEL",
    )
    transformer_llm_models: list[str] = Field(
        default_factory=lambda: [
            "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "google/flan-t5-large",
        ],
        validation_alias="TRANSFORMER_LLM_MODELS",
    )
    transformer_embed_model: str = Field(
        "intfloat/e5-large-v2",
        validation_alias="TRANSFORMER_EMBED_MODEL",
    )
    transformer_device: str = Field("cpu", validation_alias="TRANSFORMER_DEVICE")
    transformer_max_new_tokens: int = Field(512, validation_alias="TRANSFORMER_MAX_NEW_TOKENS")

    data_root: DirectoryPath = Field(Path("data"), validation_alias="DATA_ROOT")
    raw_files_dir: DirectoryPath = Field(
        default_factory=lambda: Path("data/raw_files"),
        validation_alias="RAW_FILES_DIR",
    )
    processed_files_dir: DirectoryPath = Field(
        default_factory=lambda: Path("data/processed_files"),
        validation_alias="PROCESSED_FILES_DIR",
    )
    uploaded_files_dir: DirectoryPath = Field(
        default_factory=lambda: Path("data/uploaded_files"),
        validation_alias="UPLOADED_FILES_DIR",
    )

    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")
    docs_base_url: AnyHttpUrl | None = Field(default=None, validation_alias="DOCS_BASE_URL")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()  # type: ignore[arg-type]


settings = get_settings()
