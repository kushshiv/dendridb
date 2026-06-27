import pytest
from pydantic import ValidationError

from dendridb.api.schemas.episode import EpisodeCreate, EpisodicEventCreate


@pytest.mark.unit
def test_episode_create_requires_session():
    with pytest.raises(ValidationError):
        EpisodeCreate(namespace="team-a", session_id="", metadata={})


@pytest.mark.unit
def test_episodic_event_create_requires_content():
    with pytest.raises(ValidationError):
        EpisodicEventCreate(content="")


@pytest.mark.unit
def test_episodic_event_create_accepts_provenance():
    payload = EpisodicEventCreate(
        content="User clicked submit",
        event_type="action",
        source="ui",
        provenance={"element_id": "btn-submit"},
    )
    assert payload.provenance["element_id"] == "btn-submit"
