"""Utility methods for text normalization."""
import re

WHITESPACE_RE = re.compile(r"\s+")


def normalize_spaces(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()
