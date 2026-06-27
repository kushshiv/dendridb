"""Promotion rules for semantic memory."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class PromotionAction(StrEnum):
    CREATE = "create"
    MERGE = "merge"
    VERSION = "version"


@dataclass(frozen=True)
class PromotionDecision:
    action: PromotionAction
    next_version: int
    next_confidence: float


def decide_promotion(
    *,
    has_active: bool,
    existing_content: str | None,
    existing_confidence: float | None,
    existing_version: int | None,
    new_content: str,
    new_confidence: float,
) -> PromotionDecision:
    """Decide how to apply a promotion given an optional active semantic record."""
    if not has_active:
        return PromotionDecision(
            action=PromotionAction.CREATE,
            next_version=1,
            next_confidence=new_confidence,
        )

    assert existing_content is not None
    assert existing_confidence is not None
    assert existing_version is not None

    if existing_content.strip() == new_content.strip():
        return PromotionDecision(
            action=PromotionAction.MERGE,
            next_version=existing_version,
            next_confidence=max(existing_confidence, new_confidence),
        )

    return PromotionDecision(
        action=PromotionAction.VERSION,
        next_version=existing_version + 1,
        next_confidence=new_confidence,
    )


def promotion_action_label(action: PromotionAction) -> Literal["created", "merged", "versioned"]:
    return {
        PromotionAction.CREATE: "created",
        PromotionAction.MERGE: "merged",
        PromotionAction.VERSION: "versioned",
    }[action]
