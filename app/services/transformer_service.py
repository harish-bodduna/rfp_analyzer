"""Transformer utilities for generation, summarization, and embeddings."""
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer
from transformers import pipeline

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

CAUSAL_KEYWORDS = (
    "mistral",
    "llama",
    "mixtral",
    "phi",
    "qwen",
    "falcon",
    "mpt",
)

SUMMARIZE_PROMPT = (
    "You will receive excerpts from a procurement document. Summarize the content in <=120 words focusing on details "
    "relevant to the trait \"{trait}\". Use concise sentences and avoid adding assumptions.\n\n"
    "CONTEXT:\n{context}\n\nSUMMARY:"
)


def _normalize_device(device: str) -> str | int:
    dev = (device or "cpu").strip().lower()
    if dev in {"cpu", "-1"}:
        return -1
    if dev.startswith("cuda") or dev.startswith("mps"):
        return dev
    try:
        return int(dev)
    except ValueError:
        return dev


def _is_causal_model(model_name: str) -> bool:
    lowered = model_name.lower()
    return any(keyword in lowered for keyword in CAUSAL_KEYWORDS)


@lru_cache(maxsize=4)
def _generation_pipeline(model_name: str):
    device = _normalize_device(settings.transformer_device)
    task = "text-generation" if _is_causal_model(model_name) else "text2text-generation"
    logger.info("Loading transformer generator %s (%s) on %s", model_name, task, device)
    return pipeline(
        task,
        model=model_name,
        device=device,
        trust_remote_code=True,
    )


@lru_cache
def _embedding_model() -> SentenceTransformer:
    device = settings.transformer_device
    logger.info("Loading transformer embedding model %s on %s", settings.transformer_embed_model, device)
    return SentenceTransformer(settings.transformer_embed_model, device=device)


def generate_text(
    prompt: str,
    model_name: str | None = None,
    *,
    max_new_tokens: int | None = None,
) -> str:
    model_to_use = model_name or settings.transformer_llm_model
    generator = _generation_pipeline(model_to_use)
    is_causal = _is_causal_model(model_to_use)
    kwargs = {
        "max_new_tokens": max_new_tokens or settings.transformer_max_new_tokens,
        "do_sample": False,
        "temperature": 0.1,
    }
    if is_causal:
        kwargs["return_full_text"] = False
    result = generator(prompt, **kwargs)
    if not result:
        return ""
    if is_causal:
        output = result[0].get("generated_text", "")
    else:
        output = result[0].get("generated_text") or result[0].get("summary_text") or ""
    return output.strip()


def summarize_text(text: str, trait: str) -> str:
    snippet = text.strip()
    if not snippet:
        return ""
    prompt = SUMMARIZE_PROMPT.format(trait=trait, context=snippet[:4000])
    try:
        return generate_text(prompt, max_new_tokens=200).strip()
    except Exception as exc:  # pragma: no cover
        logger.warning("Summarization failed: %s", exc)
        return ""


def embed_text_local(text: str) -> list[float]:
    model = _embedding_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()
