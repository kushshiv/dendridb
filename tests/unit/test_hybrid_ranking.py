from datetime import UTC, datetime, timedelta

import pytest

from dendridb.ranking.hybrid import (
    RankingWeights,
    build_recall_summary,
    compute_hybrid_score,
    recency_score,
    salience_score,
)


def test_salience_score_defaults_to_neutral():
    assert salience_score(None) == 0.5


def test_salience_score_clamps_to_unit_range():
    assert salience_score(2.5) == 1.0
    assert salience_score(-1.0) == 0.0


def test_recency_score_decays_with_age():
    now = datetime(2026, 1, 10, tzinfo=UTC)
    recent = now - timedelta(hours=1)
    old = now - timedelta(hours=336)
    assert recency_score(recent, now=now) > recency_score(old, now=now)


def test_compute_hybrid_score_respects_weights():
    high_salience = compute_hybrid_score(
        similarity=0.5,
        recency=0.5,
        salience=1.0,
        association=0.0,
        weights=RankingWeights(similarity=0.1, recency=0.1, salience=0.8, association=0.0),
    )
    low_salience = compute_hybrid_score(
        similarity=0.5,
        recency=0.5,
        salience=0.0,
        association=0.0,
        weights=RankingWeights(similarity=0.1, recency=0.1, salience=0.8, association=0.0),
    )
    assert high_salience.score > low_salience.score
    assert high_salience.contributions["salience"] > low_salience.contributions["salience"]


def test_build_recall_summary_mentions_primary_factor():
    summary = build_recall_summary(
        {
            "similarity": 0.4,
            "recency": 0.05,
            "salience": 0.1,
            "association": 0.02,
        }
    )
    assert "semantic similarity" in summary


def test_ranking_weights_normalize():
    weights = RankingWeights(similarity=2, recency=2, salience=2, association=2).normalized()
    assert weights.similarity == pytest.approx(0.25)
    assert weights.recency == pytest.approx(0.25)
