"""Trait extraction orchestrator."""
from __future__ import annotations

import re
from functools import lru_cache

from openai import OpenAI

from app.core.config import settings
from app.core.logging import get_logger
from app.services.transformer_service import generate_text
from app.utils.prompts import TRAIT_PROMPT_REGISTRY

logger = get_logger(__name__)

LLAMA3_MARKERS = ("llama-3", "llama3")


def _build_prompt(trait_type: str, context: str, model_name: str | None = None) -> str:
    instruction = TRAIT_PROMPT_REGISTRY.get(trait_type, f"Extract the trait: {trait_type}.")
    system_prompt = (
        "You are an expert government procurement analyst. Read the provided summary and evidence carefully. "
        "Respond with the requested value only. Do not add commentary or extra sentences. "
        "If the answer is not explicitly stated, reply with 'N/A'."
    )
    lowered = (model_name or "").lower()
    if any(marker in lowered for marker in LLAMA3_MARKERS):
        return (
            "<|begin_of_text|>"
            "<|start_header_id|>system<|end_header_id|>\n"
            f"{system_prompt}\n"
            "<|eot_id|>"
            "<|start_header_id|>user<|end_header_id|>\n"
            f"Context:\n{context}\n\n"
            f"Question: {instruction}\n"
            "Answer with the value only.\n"
            "<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\n"
        )
    return (
        "[INST]\n"
        f"<<SYS>>\n{system_prompt}\n<</SYS>>\n"
        f"Context:\n{context}\n\n"
        f"Question: {instruction}\n"
        "Answer with the value only.\n"
        "[/INST]"
    )


@lru_cache
def _client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=settings.openai_api_key)


def _call_openai(prompt: str) -> str:
    response = _client().responses.create(
        model=settings.openai_llm_model,
        input=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return response.output[0].content[0].text  # type: ignore[index]


def _call_transformer(prompt: str, model_name: str | None = None) -> str:
    return generate_text(prompt, model_name=model_name)


_NOISE_PATTERNS = [
    r"\[/?INST\]",
    r"<\|/?begin_of_text\|>",
    r"<\|/?eot_id\|>",
    r"<\|start_header_id\|>[^<]+<\|end_header_id\|>",
    r"<<SYS>>",
    r"<</SYS>>",
    r"\bContext:\b",
]


def _clean_response_text(text: str) -> str:
    cleaned = text.strip()
    for pattern in _NOISE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    # collapse excessive whitespace but keep punctuation
    cleaned = re.sub(r"\s+", " ", cleaned)
    # keep only the first sentence/line if multiple answers were returned
    if "\n" in cleaned:
        cleaned = cleaned.split("\n", 1)[0].strip()
    return cleaned


def _parse_response(trait_type: str, text: str) -> dict:
    value = _clean_response_text(text)
    if not value or value.lower() in {"", "n/a", "not available"}:
        value = None
    return {
        "value": value,
        "confidence": None,
        "pages": None,
        "evidence": None,
        "details": None,
    }


def extract_trait(trait_type: str, context: str) -> dict:
    """Call configured LLM provider to extract a trait from provided context."""

    model_candidates = settings.transformer_llm_models or [settings.transformer_llm_model]
    for model_name in model_candidates:
        prompt = _build_prompt(
            trait_type,
            context,
            model_name if settings.llm_provider == "transformers" else None,
        )
        if settings.llm_provider == "transformers":
            logger.debug("Extracting %s with transformer model %s", trait_type, model_name)
            text = _call_transformer(prompt, model_name=model_name)
        else:
            text = _call_openai(prompt)
        data = _parse_response(trait_type, text)
        if data["value"] is not None:
            if model_name != model_candidates[0]:
                logger.info("Trait %s answered by fallback model %s", trait_type, model_name)
            return data
    return {"value": None, "confidence": None, "pages": None, "evidence": None, "details": None}
