from uuid import uuid4

import pytest
from pydantic import ValidationError

from dendridb.api.schemas.semantic_memory import SemanticMemoryCreate


def test_semantic_memory_create_validates_confidence_bounds():
    with pytest.raises(ValidationError):
        SemanticMemoryCreate(
            namespace="team-a",
            key="fact-1",
            content="Some fact",
            confidence=1.5,
        )


def test_semantic_memory_create_accepts_evidence_links():
    episode_id = uuid4()
    payload = SemanticMemoryCreate(
        namespace="team-a",
        key="fact-1",
        content="Some fact",
        evidence=[{"source_type": "episode", "source_id": episode_id}],
    )
    assert payload.evidence[0].source_id == episode_id
