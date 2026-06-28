"""Pure consolidation helpers."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from uuid import UUID

from dendridb.memory.auto_link import content_similarity

_MERGED_STATUS = "merged"
_NORMALIZE_PATTERN = re.compile(r"\s+")


def normalize_content(text: str) -> str:
    return _NORMALIZE_PATTERN.sub(" ", text.strip().lower())


def is_merged_record(metadata: dict) -> bool:
    return metadata.get("consolidation_status") == _MERGED_STATUS


def pattern_key_for_content(content: str) -> str:
    digest = hashlib.sha256(normalize_content(content).encode()).hexdigest()
    return f"pattern-{digest[:12]}"


def pattern_confidence(occurrences: int) -> float:
    return min(0.95, 0.5 + (0.1 * occurrences))


@dataclass(frozen=True)
class DuplicatePair:
    keep_id: UUID
    merge_id: UUID
    similarity: float


@dataclass(frozen=True)
class RepeatedPattern:
    content: str
    key: str
    confidence: float
    event_ids: tuple[UUID, ...]
    episode_ids: tuple[UUID, ...]


def choose_canonical_record(
    left_id: UUID,
    left_salience: float | None,
    left_created_at,
    right_id: UUID,
    right_salience: float | None,
    right_created_at,
) -> tuple[UUID, UUID]:
    left_score = left_salience if left_salience is not None else 0.5
    right_score = right_salience if right_salience is not None else 0.5
    if left_score > right_score:
        return left_id, right_id
    if right_score > left_score:
        return right_id, left_id
    if left_created_at >= right_created_at:
        return left_id, right_id
    return right_id, left_id


def find_duplicate_pairs(
    records: list[tuple[UUID, str, float | None, object, dict]],
    *,
    similarity_threshold: float,
) -> list[DuplicatePair]:
    active = [record for record in records if not is_merged_record(record[4])]
    pairs: list[DuplicatePair] = []
    seen_merge_ids: set[UUID] = set()

    for index, left in enumerate(active):
        left_id, left_content, left_salience, left_created_at, _ = left
        for right in active[index + 1 :]:
            right_id, right_content, right_salience, right_created_at, _ = right
            similarity = content_similarity(left_content, right_content)
            if similarity < similarity_threshold:
                continue
            keep_id, merge_id = choose_canonical_record(
                left_id,
                left_salience,
                left_created_at,
                right_id,
                right_salience,
                right_created_at,
            )
            if merge_id in seen_merge_ids:
                continue
            seen_merge_ids.add(merge_id)
            pairs.append(DuplicatePair(keep_id=keep_id, merge_id=merge_id, similarity=similarity))
    return pairs


def find_repeated_patterns(
    events: list[tuple[UUID, UUID, str]],
    *,
    min_occurrences: int,
) -> list[RepeatedPattern]:
    grouped: dict[str, list[tuple[UUID, UUID, str]]] = {}
    for episode_id, event_id, content in events:
        key = normalize_content(content)
        if not key:
            continue
        grouped.setdefault(key, []).append((episode_id, event_id, content))

    patterns: list[RepeatedPattern] = []
    for _normalized, items in grouped.items():
        if len(items) < min_occurrences:
            continue
        representative = max((content for _, _, content in items), key=len)
        patterns.append(
            RepeatedPattern(
                content=representative,
                key=pattern_key_for_content(representative),
                confidence=pattern_confidence(len(items)),
                event_ids=tuple(event_id for _, event_id, _ in items),
                episode_ids=tuple(dict.fromkeys(episode_id for episode_id, _, _ in items)),
            )
        )
    return sorted(patterns, key=lambda pattern: (-pattern.confidence, pattern.key))
