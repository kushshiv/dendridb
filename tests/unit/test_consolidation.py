from datetime import UTC, datetime
from uuid import uuid4

from dendridb.memory.consolidation import (
    choose_canonical_record,
    find_duplicate_pairs,
    find_repeated_patterns,
    is_merged_record,
    pattern_key_for_content,
)


def test_find_repeated_patterns_requires_min_occurrences():
    episode_id = uuid4()
    events = [
        (episode_id, uuid4(), "User prefers dark mode"),
        (episode_id, uuid4(), "user prefers dark mode"),
    ]
    assert find_repeated_patterns(events, min_occurrences=3) == []
    patterns = find_repeated_patterns(events, min_occurrences=2)
    assert len(patterns) == 1
    assert patterns[0].key == pattern_key_for_content("User prefers dark mode")


def test_find_duplicate_pairs_marks_lower_salience_for_merge():
    keep_id = uuid4()
    merge_id = uuid4()
    now = datetime.now(UTC)
    pairs = find_duplicate_pairs(
        [
            (keep_id, "billing invoice timing question", 2.0, now, {}),
            (merge_id, "billing invoice timing question", 0.5, now, {}),
        ],
        similarity_threshold=0.8,
    )
    assert len(pairs) == 1
    assert pairs[0].keep_id == keep_id
    assert pairs[0].merge_id == merge_id


def test_is_merged_record():
    assert is_merged_record({"consolidation_status": "merged"}) is True
    assert is_merged_record({}) is False


def test_choose_canonical_record_prefers_newer_when_salience_equal():
    older_id = uuid4()
    newer_id = uuid4()
    older = datetime(2026, 1, 1, tzinfo=UTC)
    newer = datetime(2026, 1, 2, tzinfo=UTC)
    keep, merge = choose_canonical_record(
        older_id,
        1.0,
        older,
        newer_id,
        1.0,
        newer,
    )
    assert keep == newer_id
    assert merge == older_id
