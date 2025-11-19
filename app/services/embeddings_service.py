"""Embedding utilities."""
from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from app.core.config import settings
from app.services.transformer_service import embed_text_local


@lru_cache
def _client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=settings.openai_api_key)


def embed_text(text: str) -> list[float]:
    """Generate embeddings via configured provider."""

    if settings.embed_provider == "transformers":
        return embed_text_local(text)

    response = _client().embeddings.create(model=settings.openai_embed_model, input=text)
    return response.data[0].embedding
