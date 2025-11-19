"""Tokenization helpers built on tiktoken."""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Sequence

import tiktoken


DEFAULT_ENCODING = "cl100k_base"


@lru_cache(maxsize=8)
def _encoding(model: str | None = None) -> tiktoken.Encoding:
    """Return a cached tokenizer encoding."""

    if model:
        try:
            return tiktoken.encoding_for_model(model)
        except KeyError:
            pass
    return tiktoken.get_encoding(DEFAULT_ENCODING)


def count_tokens(text: str, model: str | None = None) -> int:
    """Return approximate token count for text."""

    if not text:
        return 0
    encoding = _encoding(model)
    return len(encoding.encode(text))


def trim_text(text: str, max_tokens: int, model: str | None = None) -> str:
    """Trim text to fit within max_tokens."""

    if max_tokens <= 0:
        return ""
    encoding = _encoding(model)
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return encoding.decode(tokens[:max_tokens])


def last_tokens(text: str, tail_tokens: int, model: str | None = None) -> str:
    """Return the last N tokens of the provided text."""

    if tail_tokens <= 0:
        return ""
    encoding = _encoding(model)
    tokens = encoding.encode(text)
    if len(tokens) <= tail_tokens:
        return text
    return encoding.decode(tokens[-tail_tokens:])


def join_with_budget(
    blocks: Iterable[str],
    max_tokens: int,
    separator: str = "\n\n---\n\n",
    model: str | None = None,
) -> tuple[str, list[str]]:
    """Join text blocks until reaching the token budget.

    Returns the concatenated string and the list of blocks that fit.
    """

    encoding = _encoding(model)
    selected: list[str] = []
    token_total = 0
    parts: list[str] = []
    sep_tokens = count_tokens(separator, model)

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        block_tokens = len(encoding.encode(block))
        additional = block_tokens if not parts else block_tokens + sep_tokens

        if token_total + additional > max_tokens:
            if not parts:
                # Force include trimmed block so we always return something.
                trimmed = trim_text(block, max_tokens)
                selected.append(block)
                return trimmed, selected
            break

        parts.append(block)
        selected.append(block)
        token_total += additional

    return separator.join(parts), selected


def split_text_by_tokens(text: str, max_tokens: int, overlap: int = 0, model: str | None = None) -> list[str]:
    """Split long text into slices constrained by token counts."""

    if not text:
        return []
    encoding = _encoding(model)
    token_ids = encoding.encode(text)
    if len(token_ids) <= max_tokens:
        return [text]

    chunks: list[str] = []
    start = 0
    end = max_tokens
    while start < len(token_ids):
        chunk_tokens = token_ids[start:end]
        chunks.append(encoding.decode(chunk_tokens))
        if end >= len(token_ids):
            break
        start = end - overlap if overlap else end
        if start < 0:
            start = 0
        end = start + max_tokens
    return chunks


def cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Compute cosine similarity between two equal-length vectors."""

    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

