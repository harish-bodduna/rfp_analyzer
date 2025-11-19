"""Chunk retrieval helpers."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from sqlmodel import Session, select

from app.db.models import Chunk
from app.services.embeddings_service import embed_text
from app.services.transformer_service import summarize_text
from app.utils.prompts import TRAIT_PROMPT_REGISTRY, TRAIT_RETRIEVAL_QUERIES
from app.utils.tokenization import (
    count_tokens,
    cosine_similarity,
    join_with_budget,
    trim_text,
)

MAX_CONTEXT_CHUNKS = 5
EARLY_PAGE_TRAITS = {"title", "due_date"}
EARLY_PAGE_MAX = 4
EVIDENCE_TOKEN_LIMIT = 400
SUMMARY_TOKEN_LIMIT = 800

TRAIT_KEYWORDS = {
    "title": ["request for proposal", "rfp", "rfq", "invitation"],
    "due_date": ["due", "deadline", "submission"],
    "point_of_contact": ["contact", "poc", "questions"],
    "submitted_to": ["submit", "addressed", "agency", "department"],
    "submission_method": ["submit via", "portal", "email", "deliver"],
    "submission_checklist": ["checklist", "include", "required documents"],
    "questions_poc": ["questions", "clarifications", "contact"],
    "receipt_of_amendments": ["acknowledge", "addenda", "amendments"],
    "notary_needed": ["notary", "notarized", "seal"],
    "resumes_needed": ["resume", "curriculum vitae", "cv"],
    "references_needed": ["reference", "client reference"],
    "scope_of_work": ["scope of work", "services", "deliverables"],
    "categorization": ["category", "classification", "industry"],
    "insurance_needed": ["insurance", "coverage", "certificate"],
    "technical_requirements": ["requirements", "qualifications", "experience"],
}


@dataclass
class ChunkScore:
    chunk: Chunk
    score: float


def _keyword_score(content: str, keywords: Iterable[str]) -> float:
    if not keywords:
        return 0.0
    lowered = content.lower()
    hits = 0
    for keyword in keywords:
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            hits += 1
    return hits / len(keywords)


def _trait_query(trait_type: str) -> str:
    if trait_type in TRAIT_RETRIEVAL_QUERIES:
        return TRAIT_RETRIEVAL_QUERIES[trait_type]
    base = TRAIT_PROMPT_REGISTRY.get(trait_type)
    return base or f"Extract the trait {trait_type} from the RFP document."


def _filter_early_pages(chunks: list[Chunk], trait_type: str) -> list[Chunk]:
    if trait_type not in EARLY_PAGE_TRAITS:
        return chunks
    early_chunks = [
        chunk
        for chunk in chunks
        if (chunk.page_start or 1) <= EARLY_PAGE_MAX
    ]
    return early_chunks or chunks


def _trim_by_paragraphs(text: str, max_tokens: int) -> str:
    if not text or max_tokens <= 0:
        return ""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return trim_text(text, max_tokens)

    kept: list[str] = []
    total_tokens = 0
    for paragraph in paragraphs:
        para_tokens = count_tokens(paragraph)
        if para_tokens > max_tokens:
            if not kept:
                kept.append(trim_text(paragraph, max_tokens))
            break
        if total_tokens + para_tokens > max_tokens:
            break
        kept.append(paragraph)
        total_tokens += para_tokens

    if not kept:
        kept.append(trim_text(paragraphs[0], max_tokens))

    return "\n\n".join(kept)


def _rank_chunks(chunks: list[Chunk], trait_type: str) -> list[ChunkScore]:
    if not chunks:
        return []

    query_embedding = embed_text(_trait_query(trait_type))
    keywords = TRAIT_KEYWORDS.get(trait_type, [])
    ranked: list[ChunkScore] = []

    for chunk in chunks:
        embedding = chunk.embedding
        vec_score = cosine_similarity(embedding, query_embedding) if embedding else 0.0
        key_score = _keyword_score(chunk.content, keywords)
        combined = (0.7 * vec_score) + (0.3 * key_score)
        ranked.append(ChunkScore(chunk=chunk, score=combined))

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked


def retrieve_chunks(session: Session, document_id, trait_type: str, limit: int = 5) -> list[Chunk]:
    """Rank and return top chunks for a trait."""

    statement = select(Chunk).where(Chunk.document_id == document_id)
    chunks = session.exec(statement).all()
    chunks = _filter_early_pages(chunks, trait_type)
    ranked = _rank_chunks(chunks, trait_type)
    if not ranked:
        return []
    return [item.chunk for item in ranked[:limit]]


def build_context_for_trait(
    session: Session,
    document_id,
    trait_type: str,
    *,
    token_budget: int = 800,
) -> tuple[str, list[Chunk]]:
    """Return concatenated context text and supporting chunks for a trait."""

    statement = select(Chunk).where(Chunk.document_id == document_id)
    chunks = session.exec(statement).all()
    chunks = _filter_early_pages(chunks, trait_type)
    ranked = _rank_chunks(chunks, trait_type)
    if not ranked:
        return "", []

    selected_scores = ranked[:MAX_CONTEXT_CHUNKS]
    summaries: list[str] = []
    evidence_blocks: list[str] = []
    kept_chunks: list[Chunk] = []

    for scored in selected_scores:
        chunk = scored.chunk
        content = (chunk.content or "").strip()
        if not content:
            continue
        kept_chunks.append(chunk)
        snippet = _trim_by_paragraphs(content, EVIDENCE_TOKEN_LIMIT)
        evidence_blocks.append(f"Pages {chunk.page_start}-{chunk.page_end}:\n{snippet}")
        summary_input = (
            f"Trait focus: {trait_type}\n"
            f"Pages {chunk.page_start}-{chunk.page_end}:\n"
            f"{_trim_by_paragraphs(content, SUMMARY_TOKEN_LIMIT)}"
        )
        summary = summarize_text(summary_input, trait_type)
        if not summary:
            summary = snippet
        summaries.append(f"- Pages {chunk.page_start}-{chunk.page_end}: {summary.strip()}")
        if len(kept_chunks) >= MAX_CONTEXT_CHUNKS:
            break

    if not kept_chunks:
        return "", []

    summary_section = "Focused Summaries:\n" + "\n".join(summaries)
    evidence_section, _ = join_with_budget(evidence_blocks, max_tokens=token_budget)
    context_text = f"{summary_section}\n\nSupporting Evidence:\n{evidence_section}"

    return context_text, kept_chunks
