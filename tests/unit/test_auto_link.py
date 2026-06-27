from uuid import uuid4

from dendridb.memory.auto_link import (
    build_content_similarity_candidate,
    build_metadata_match_candidate,
    content_similarity,
    metadata_overlap,
)


def test_content_similarity_for_shared_tokens():
    score = content_similarity(
        "User prefers dark mode for the dashboard",
        "Dashboard uses dark mode preference",
    )
    assert score > 0.3


def test_content_similarity_zero_for_disjoint_text():
    assert content_similarity("alpha beta", "gamma delta") == 0.0


def test_metadata_overlap_finds_shared_fields():
    score, paths = metadata_overlap(
        {"topic": "billing", "channel": "email"},
        {"topic": "billing", "priority": "high"},
    )
    assert score > 0
    assert paths == ["topic"]


def test_build_metadata_match_candidate():
    candidate = build_metadata_match_candidate(
        target_type="memory_record",
        target_id=str(uuid4()),
        overlap_score=0.5,
        shared_paths=["topic"],
    )
    assert candidate is not None
    assert candidate.edge_type == "metadata_match"
    assert "topic" in candidate.explanation


def test_build_content_similarity_candidate_respects_threshold():
    low = build_content_similarity_candidate(
        target_type="memory_record",
        target_id=str(uuid4()),
        similarity=0.2,
        threshold=0.3,
    )
    high = build_content_similarity_candidate(
        target_type="memory_record",
        target_id=str(uuid4()),
        similarity=0.6,
        threshold=0.3,
    )
    assert low is None
    assert high is not None
    assert high.weight == 0.6
