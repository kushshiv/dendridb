from datetime import UTC, datetime, timedelta

import pytest

from dendridb.memory.decay_policy import (
    DecayPolicy,
    age_hours_since,
    compute_decayed_salience,
    reinforce_salience,
    should_archive,
)
from dendridb.memory.visibility import is_active_memory, is_archived_record


@pytest.mark.unit
def test_compute_decayed_salience_halves_each_half_life():
    policy = DecayPolicy(half_life_hours=24.0)
    assert compute_decayed_salience(
        1.0, age_hours=24.0, policy=policy, pinned=False
    ) == pytest.approx(0.5)
    assert compute_decayed_salience(
        1.0, age_hours=48.0, policy=policy, pinned=False
    ) == pytest.approx(0.25)


@pytest.mark.unit
def test_pinned_memory_skips_decay():
    policy = DecayPolicy(half_life_hours=24.0)
    assert compute_decayed_salience(2.0, age_hours=1000.0, policy=policy, pinned=True) == 2.0


@pytest.mark.unit
def test_should_archive_respects_min_salience_and_pinning():
    policy = DecayPolicy(min_salience=0.1)
    assert should_archive(0.05, policy=policy, pinned=False) is True
    assert should_archive(0.2, policy=policy, pinned=False) is False
    assert should_archive(0.05, policy=policy, pinned=True) is False


@pytest.mark.unit
def test_reinforce_salience_caps_at_max():
    policy = DecayPolicy(max_salience=1.0, retrieval_strengthen_delta=0.2)
    assert reinforce_salience(0.5, policy=policy) == pytest.approx(0.7)
    assert reinforce_salience(0.95, policy=policy) == pytest.approx(1.0)


@pytest.mark.unit
def test_age_hours_since_is_non_negative():
    now = datetime(2026, 1, 2, tzinfo=UTC)
    earlier = now - timedelta(hours=3)
    assert age_hours_since(earlier, now=now) == pytest.approx(3.0)


@pytest.mark.unit
def test_visibility_helpers():
    assert is_archived_record(datetime.now(UTC)) is True
    assert is_archived_record(None) is False
    assert is_active_memory(metadata={}, archived_at=None) is True
    assert is_active_memory(metadata={"consolidation_status": "merged"}, archived_at=None) is False
    assert is_active_memory(metadata={}, archived_at=datetime.now(UTC)) is False
