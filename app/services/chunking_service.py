"""Create semantic chunks from parsed pages."""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Iterable

from app.core.logging import get_logger
from app.utils.tokenization import count_tokens, split_text_by_tokens

logger = get_logger(__name__)

MULTISPACE_RE = re.compile(r"[ \t]{2,}")


@dataclass
class ChunkPayload:
    content: str
    page_start: int
    page_end: int
    token_count: int
    summary: str | None = None
    metadata: dict = field(default_factory=dict)


def _normalize_paragraph(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    text = text.replace("\r", " ")
    text = text.replace("\n", " ")
    text = MULTISPACE_RE.sub(" ", text)
    return text


def _split_paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    for block in text.split("\n\n"):
        normalized = _normalize_paragraph(block)
        if normalized:
            paragraphs.append(normalized)
    return paragraphs


def chunk_pages(pages: Iterable[dict], max_tokens: int = 400) -> list[ChunkPayload]:
    """Naive chunking by paragraphs and token windows."""

    chunks: list[ChunkPayload] = []
    buffer: list[str] = []
    tokens = 0
    page_start = None
    last_page = None

    for page in pages:
        paragraphs = _split_paragraphs(page["text"])
        for paragraph in paragraphs:
            paragraph_tokens = len(paragraph.split())
            if page_start is None:
                page_start = page["page_number"]
            last_page = page["page_number"]

            if tokens + paragraph_tokens > max_tokens and buffer:
                chunks.append(
                    ChunkPayload(
                        content="\n\n".join(buffer),
                        page_start=page_start or last_page or 1,
                        page_end=last_page or page_start or 1,
                        token_count=tokens,
                    )
                )
                buffer = []
                tokens = 0
                page_start = page["page_number"]

            buffer.append(paragraph)
            tokens += paragraph_tokens

    if buffer:
        chunks.append(
            ChunkPayload(
                content="\n\n".join(buffer),
                page_start=page_start or 1,
                page_end=last_page or page_start or 1,
                token_count=tokens,
            )
        )
    return chunks


def chunk_elements(
    elements: Iterable[dict],
    *,
    max_tokens: int = 900,
    min_tokens: int = 120,
    overlap_tokens: int = 0,
) -> list[ChunkPayload]:
    """Chunk layout-aware elements with token budgets."""

    chunk_payloads: list[ChunkPayload] = []
    buffer: list[dict] = []
    buffer_tokens = 0

    def _flush_buffer() -> None:
        nonlocal buffer, buffer_tokens
        if not buffer:
            return
        pages = [num for item in buffer for num in item.get("pages", [])]
        page_start = min(pages) if pages else 1
        page_end = max(pages) if pages else page_start
        content = "\n\n".join(item["text"] for item in buffer)
        metadata = {
            "element_ids": [item["id"] for item in buffer],
            "element_types": list({item["type"] for item in buffer}),
            "source_pages": pages,
        }
        chunk_payloads.append(
            ChunkPayload(
                content=content,
                page_start=page_start,
                page_end=page_end,
                token_count=buffer_tokens,
                metadata=metadata,
            )
        )
        if overlap_tokens > 0 and content:
            overlap_texts = split_text_by_tokens(content, overlap_tokens, 0)
            if overlap_texts:
                overlap_id = f"{metadata['element_ids'][-1]}:overlap"
                tail_pages = pages[-1:] if pages else []
                buffer = [
                    {
                        "id": overlap_id,
                        "text": overlap_texts[-1],
                        "type": "overlap",
                        "pages": tail_pages,
                    }
                ]
                buffer_tokens = count_tokens(buffer[0]["text"])
            else:
                buffer = []
                buffer_tokens = 0
        else:
            buffer = []
            buffer_tokens = 0

    for element in elements:
        text = _normalize_paragraph(element.get("text") or "")
        if not text:
            continue
        element_id = element.get("element_id") or element.get("id") or str(uuid.uuid4())
        pages = element.get("page_numbers") or element.get("pages") or []
        pages = [int(num) for num in pages if isinstance(num, (int, float))]
        base = {
            "id": element_id,
            "type": element.get("element_type") or element.get("type") or "Unknown",
            "pages": pages,
        }
        segments = [text]
        token_count = count_tokens(text)
        if token_count > max_tokens:
            segments = split_text_by_tokens(text, max_tokens, overlap_tokens)
        for idx, segment in enumerate(segments):
            segment_tokens = count_tokens(segment)
            segment_payload = {
                **base,
                "id": f"{base['id']}:{idx}" if len(segments) > 1 else base["id"],
                "text": segment,
            }
            if buffer_tokens + segment_tokens > max_tokens and buffer:
                _flush_buffer()
            buffer.append(segment_payload)
            buffer_tokens += segment_tokens
            if buffer_tokens >= max_tokens:
                _flush_buffer()

    if buffer and (buffer_tokens >= min_tokens or not chunk_payloads):
        _flush_buffer()

    return chunk_payloads
