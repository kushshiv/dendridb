import pytest
from pydantic import ValidationError

from dendridb.api.schemas.memory_record import MemoryRecordCreate


@pytest.mark.unit
def test_memory_record_create_requires_namespace():
    with pytest.raises(ValidationError):
        MemoryRecordCreate(namespace="", content="hello")


@pytest.mark.unit
def test_memory_record_create_requires_content():
    with pytest.raises(ValidationError):
        MemoryRecordCreate(namespace="default", content="")


@pytest.mark.unit
def test_memory_record_create_defaults():
    payload = MemoryRecordCreate(namespace="team-a", content="remember this")
    assert payload.memory_type == "generic"
    assert payload.metadata == {}


@pytest.mark.unit
def test_memory_record_create_validates_confidence_range():
    with pytest.raises(ValidationError):
        MemoryRecordCreate(namespace="team-a", content="x", confidence=1.5)


@pytest.mark.unit
def test_memory_record_create_accepts_provenance():
    payload = MemoryRecordCreate(
        namespace="team-a",
        content="event happened",
        source="chat",
        actor_id="user-1",
        provenance={"session_id": "sess-1", "message_id": "msg-9"},
        metadata={"tags": ["important"]},
    )
    assert payload.provenance["session_id"] == "sess-1"
    assert payload.metadata["tags"] == ["important"]
