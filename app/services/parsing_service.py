"""PDF parsing and layout-aware extraction."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import fitz  # type: ignore

from app.core.logging import get_logger
from app.utils.tokenization import count_tokens

logger = get_logger(__name__)

try:  # pragma: no cover - optional dependency handling
    from unstructured.partition.pdf import partition_pdf
except Exception:  # pragma: no cover - defensive import
    partition_pdf = None  # type: ignore[assignment]


@dataclass
class ParsedPage:
    page_number: int
    text: str
    tokens: int


@dataclass
class ParsedElement:
    element_id: str
    text: str
    element_type: str
    page_numbers: list[int]
    tokens: int
    metadata: dict
    structured_text: str | None = None


def extract_pages(pdf_path: str) -> Iterator[ParsedPage]:
    """Yield pages with text and token counts."""

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(pdf_path)

    document = fitz.open(pdf_path)
    for number, page in enumerate(document, start=1):
        text = page.get_text("text")
        tokens = count_tokens(text)
        yield ParsedPage(page_number=number, text=text, tokens=tokens)
    document.close()


def _extract_elements(pdf_path: str) -> list[ParsedElement]:
    """Run unstructured parsing to capture layout-aware elements."""

    if partition_pdf is None:
        logger.warning("unstructured library unavailable; skipping element extraction")
        return []

    elements: list[ParsedElement] = []
    try:
        parsed = partition_pdf(
            filename=pdf_path,
            include_metadata=True,
            infer_table_structure=True,
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("unstructured parsing failed: %s", exc)
        return []

    for element in parsed:
        text = (getattr(element, "text", "") or "").strip()
        metadata_obj = getattr(element, "metadata", None)
        metadata = metadata_obj.to_dict() if metadata_obj else {}
        element_type = getattr(element, "category", element.__class__.__name__)
        structured_text = metadata.get("text_as_markdown") or metadata.get("text_as_html")
        if element_type == "Table" and structured_text:
            text = structured_text
        if not text:
            continue
        page_numbers = []
        if "page_number" in metadata and metadata["page_number"]:
            page_numbers = [int(metadata["page_number"])]
        elif "page_numbers" in metadata and metadata["page_numbers"]:
            page_numbers = []
            for raw_value in metadata["page_numbers"]:
                try:
                    page_numbers.append(int(raw_value))
                except (TypeError, ValueError):
                    continue
        tokens = count_tokens(text)
        fallback_page = metadata.get("page_number") or 1
        try:
            fallback_page = int(fallback_page)
        except (TypeError, ValueError):
            fallback_page = 1
        elements.append(
            ParsedElement(
                element_id=str(uuid.uuid4()),
                text=text,
                element_type=element_type,
                page_numbers=page_numbers or [fallback_page],
                tokens=tokens,
                metadata=metadata,
                structured_text=structured_text,
            )
        )
    return elements


def summarize_document(pdf_path: str) -> dict:
    """Return document stats, layout-aware elements, and page snapshots."""

    pages = list(extract_pages(pdf_path))
    total_tokens = sum(page.tokens for page in pages)
    elements = _extract_elements(pdf_path)

    if not elements:
        # Fallback: treat each page as an element for downstream chunking.
        for page in pages:
            elements.append(
                ParsedElement(
                    element_id=str(uuid.uuid4()),
                    text=page.text,
                    element_type="Page",
                    page_numbers=[page.page_number],
                    tokens=page.tokens,
                    metadata={"source": "page_fallback"},
                    structured_text=None,
                )
            )

    return {
        "page_count": len(pages),
        "token_count": total_tokens,
        "pages": [page.__dict__ for page in pages],
        "elements": [element.__dict__ for element in elements],
    }
