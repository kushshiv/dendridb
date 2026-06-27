import pytest

from dendridb.memory.embeddings import embed_text


def test_embed_text_is_normalized():
    vector = embed_text("billing invoice payment")
    norm = sum(value * value for value in vector) ** 0.5
    assert norm == pytest.approx(1.0, abs=1e-6)


def test_embed_text_similar_content_has_higher_cosine_similarity():
    left = embed_text("billing invoice payment")
    right = embed_text("invoice payment billing details")
    unrelated = embed_text("dark mode dashboard theme")

    def cosine(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b, strict=True))

    assert cosine(left, right) > cosine(left, unrelated)
