"""Local deterministic text embedder for development and tests."""

from __future__ import annotations

import math
import re

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


def embed_text(text: str, *, dimensions: int = 384) -> list[float]:
    """Hash tokens into a normalized vector for cosine similarity search."""
    vector = [0.0] * dimensions
    for token in tokenize(text):
        index = hash(token) % dimensions
        vector[index] += 1.0

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
