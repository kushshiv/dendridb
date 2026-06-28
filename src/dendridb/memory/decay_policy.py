"""Decay and retrieval-strengthening policies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DecayPolicy:
    half_life_hours: float = 168.0
    min_salience: float = 0.1
    max_salience: float = 10.0
    retrieval_strengthen_delta: float = 0.1


def effective_salience(salience: float | None) -> float:
    if salience is None:
        return 0.5
    return salience


def compute_decayed_salience(
    salience: float | None,
    *,
    age_hours: float,
    policy: DecayPolicy,
    pinned: bool,
) -> float:
    if pinned:
        return effective_salience(salience)
    base = effective_salience(salience)
    if policy.half_life_hours <= 0:
        return base
    decay_factor = 0.5 ** (age_hours / policy.half_life_hours)
    return max(0.0, base * decay_factor)


def should_archive(
    salience: float,
    *,
    policy: DecayPolicy,
    pinned: bool,
) -> bool:
    if pinned:
        return False
    return salience < policy.min_salience


def reinforce_salience(
    salience: float | None,
    *,
    policy: DecayPolicy,
) -> float:
    return min(
        policy.max_salience, effective_salience(salience) + policy.retrieval_strengthen_delta
    )


def age_hours_since(reference: datetime, *, now: datetime) -> float:
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=now.tzinfo)
    return max(0.0, (now - reference).total_seconds() / 3600)
