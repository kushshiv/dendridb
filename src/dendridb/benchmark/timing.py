"""Timing helpers for benchmark scenarios."""

from __future__ import annotations

import statistics
import time
from collections.abc import Awaitable, Callable
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import TypeVar

T = TypeVar("T")


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@contextmanager
def measure_seconds():
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start


async def measure_async(callable_: Callable[[], Awaitable[T]]) -> tuple[T, float]:
    start = time.perf_counter()
    result = await callable_()
    elapsed = time.perf_counter() - start
    return result, elapsed


def summarize_seconds(samples: list[float]) -> dict[str, float]:
    if not samples:
        return {
            "count": 0.0,
            "total_seconds": 0.0,
            "mean_seconds": 0.0,
            "min_seconds": 0.0,
            "max_seconds": 0.0,
            "p50_seconds": 0.0,
            "p95_seconds": 0.0,
        }

    ordered = sorted(samples)
    count = len(ordered)
    p50_index = max(0, int(count * 0.5) - 1)
    p95_index = max(0, int(count * 0.95) - 1)
    return {
        "count": float(count),
        "total_seconds": sum(ordered),
        "mean_seconds": statistics.mean(ordered),
        "min_seconds": ordered[0],
        "max_seconds": ordered[-1],
        "p50_seconds": ordered[p50_index],
        "p95_seconds": ordered[p95_index],
    }


def to_milliseconds(seconds: float) -> float:
    return round(seconds * 1000, 3)
