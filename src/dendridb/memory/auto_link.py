"""Similarity and auto-linking helpers for memory associations."""

from __future__ import annotations

import re
from dataclasses import dataclass

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set[str]:
    return set(_TOKEN_PATTERN.findall(text.lower()))


def content_similarity(left: str, right: str) -> float:
    """Jaccard similarity over normalized word tokens."""
    left_tokens = tokenize(left)
    right_tokens = tokenize(right)
    if not left_tokens or not right_tokens:
        return 0.0
    intersection = left_tokens & right_tokens
    union = left_tokens | right_tokens
    return len(intersection) / len(union)


def metadata_overlap(left: dict, right: dict) -> tuple[float, list[str]]:
    """Return overlap score and shared key paths for flat metadata objects."""
    if not left or not right:
        return 0.0, []

    shared_paths: list[str] = []
    for key, left_value in left.items():
        if key not in right:
            continue
        right_value = right[key]
        if left_value == right_value:
            shared_paths.append(key)

    if not shared_paths:
        return 0.0, []

    union_keys = set(left) | set(right)
    score = len(shared_paths) / len(union_keys)
    return score, shared_paths


@dataclass(frozen=True)
class AutoLinkCandidate:
    target_type: str
    target_id: str
    edge_type: str
    weight: float
    explanation: str


def build_metadata_match_candidate(
    *,
    target_type: str,
    target_id: str,
    overlap_score: float,
    shared_paths: list[str],
) -> AutoLinkCandidate | None:
    if overlap_score <= 0 or not shared_paths:
        return None
    paths = ", ".join(sorted(shared_paths))
    return AutoLinkCandidate(
        target_type=target_type,
        target_id=target_id,
        edge_type="metadata_match",
        weight=min(1.0, overlap_score),
        explanation=f"Shared metadata fields: {paths}",
    )


def build_content_similarity_candidate(
    *,
    target_type: str,
    target_id: str,
    similarity: float,
    threshold: float,
) -> AutoLinkCandidate | None:
    if similarity < threshold:
        return None
    return AutoLinkCandidate(
        target_type=target_type,
        target_id=target_id,
        edge_type="content_similar",
        weight=similarity,
        explanation=f"Content token similarity {similarity:.2f} (threshold {threshold:.2f})",
    )
