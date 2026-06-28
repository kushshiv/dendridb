"""Summarization hooks for consolidation."""

from __future__ import annotations

from typing import Protocol


class Summarizer(Protocol):
    def summarize(self, texts: list[str]) -> str: ...


def default_summarizer(texts: list[str]) -> str:
    """Join unique non-empty texts into a compact summary."""
    unique: list[str] = []
    seen: set[str] = set()
    for text in texts:
        cleaned = text.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique.append(cleaned)
    if not unique:
        return ""
    if len(unique) == 1:
        return unique[0]
    return "; ".join(unique[:5])
