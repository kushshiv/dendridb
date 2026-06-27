from dendridb.memory.promotion import PromotionAction, decide_promotion, promotion_action_label


def test_decide_promotion_create_when_no_active():
    decision = decide_promotion(
        has_active=False,
        existing_content=None,
        existing_confidence=None,
        existing_version=None,
        new_content="User prefers dark mode",
        new_confidence=0.7,
    )
    assert decision.action == PromotionAction.CREATE
    assert decision.next_version == 1
    assert decision.next_confidence == 0.7


def test_decide_promotion_merge_same_content():
    decision = decide_promotion(
        has_active=True,
        existing_content="User prefers dark mode",
        existing_confidence=0.6,
        existing_version=2,
        new_content="User prefers dark mode",
        new_confidence=0.85,
    )
    assert decision.action == PromotionAction.MERGE
    assert decision.next_version == 2
    assert decision.next_confidence == 0.85


def test_decide_promotion_merge_ignores_whitespace():
    decision = decide_promotion(
        has_active=True,
        existing_content="  User prefers dark mode  ",
        existing_confidence=0.9,
        existing_version=1,
        new_content="User prefers dark mode",
        new_confidence=0.5,
    )
    assert decision.action == PromotionAction.MERGE
    assert decision.next_confidence == 0.9


def test_decide_promotion_version_on_contradiction():
    decision = decide_promotion(
        has_active=True,
        existing_content="User prefers light mode",
        existing_confidence=0.8,
        existing_version=1,
        new_content="User prefers dark mode",
        new_confidence=0.75,
    )
    assert decision.action == PromotionAction.VERSION
    assert decision.next_version == 2
    assert decision.next_confidence == 0.75


def test_promotion_action_label():
    assert promotion_action_label(PromotionAction.CREATE) == "created"
    assert promotion_action_label(PromotionAction.MERGE) == "merged"
    assert promotion_action_label(PromotionAction.VERSION) == "versioned"
