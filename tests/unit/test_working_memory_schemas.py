import pytest
from pydantic import ValidationError

from dendridb.api.schemas.working_memory import WorkingMemoryCreate, WorkingMemoryUpdate


@pytest.mark.unit
def test_working_memory_create_requires_session_and_key():
    with pytest.raises(ValidationError):
        WorkingMemoryCreate(namespace="team-a", session_id="", key="ctx", content="data")


@pytest.mark.unit
def test_working_memory_create_validates_ttl():
    with pytest.raises(ValidationError):
        WorkingMemoryCreate(
            namespace="team-a",
            session_id="sess-1",
            key="ctx",
            content="data",
            ttl_seconds=0,
        )


@pytest.mark.unit
def test_working_memory_update_allows_partial_fields():
    payload = WorkingMemoryUpdate(content="updated")
    assert payload.content == "updated"
    assert payload.ttl_seconds is None
