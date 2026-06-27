"""Hybrid ranking for memory recall."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class RankingWeights:
    similarity: float = 0.5
    recency: float = 0.2
    salience: float = 0.2
    association: float = 0.1

    def normalized(self) -> RankingWeights:
        total = self.similarity + self.recency + self.salience + self.association
        if total == 0:
            return RankingWeights(similarity=1.0, recency=0.0, salience=0.0, association=0.0)
        return RankingWeights(
            similarity=self.similarity / total,
            recency=self.recency / total,
            salience=self.salience / total,
            association=self.association / total,
        )


@dataclass(frozen=True)
class RankingFactors:
    similarity: float
    recency: float
    salience: float
    association: float

    def as_dict(self) -> dict[str, float]:
        return {
            "similarity": self.similarity,
            "recency": self.recency,
            "salience": self.salience,
            "association": self.association,
        }


@dataclass(frozen=True)
class HybridScore:
    score: float
    factors: RankingFactors
    contributions: dict[str, float]


def recency_score(
    created_at: datetime,
    *,
    now: datetime | None = None,
    half_life_hours: float = 168.0,
) -> float:
    reference = now or datetime.now(UTC)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    age_hours = max(0.0, (reference - created_at).total_seconds() / 3600)
    if half_life_hours <= 0:
        return 1.0
    return 0.5 ** (age_hours / half_life_hours)


def salience_score(salience: float | None) -> float:
    if salience is None:
        return 0.5
    return max(0.0, min(1.0, salience))


def compute_hybrid_score(
    *,
    similarity: float,
    recency: float,
    salience: float,
    association: float,
    weights: RankingWeights,
) -> HybridScore:
    normalized = weights.normalized()
    factors = RankingFactors(
        similarity=max(0.0, min(1.0, similarity)),
        recency=max(0.0, min(1.0, recency)),
        salience=max(0.0, min(1.0, salience)),
        association=max(0.0, min(1.0, association)),
    )
    contributions = {
        "similarity": factors.similarity * normalized.similarity,
        "recency": factors.recency * normalized.recency,
        "salience": factors.salience * normalized.salience,
        "association": factors.association * normalized.association,
    }
    score = sum(contributions.values())
    return HybridScore(score=score, factors=factors, contributions=contributions)


def build_recall_summary(contributions: dict[str, float]) -> str:
    ranked = sorted(contributions.items(), key=lambda item: item[1], reverse=True)
    primary_factor, primary_value = ranked[0]
    labels = {
        "similarity": "semantic similarity",
        "recency": "recency",
        "salience": "salience",
        "association": "association strength",
    }
    label = labels.get(primary_factor, primary_factor.replace("_", " "))
    if primary_value <= 0:
        return "Matched with neutral ranking factors"
    secondary = ranked[1][0] if len(ranked) > 1 and ranked[1][1] > 0 else None
    if secondary is None:
        return f"Ranked primarily due to {label}"
    secondary_label = labels.get(secondary, secondary.replace("_", " "))
    return f"Ranked primarily due to {label}, with supporting {secondary_label}"
