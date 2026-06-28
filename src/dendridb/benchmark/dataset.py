"""Load benchmark datasets from JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class MemoryFixture(BaseModel):
    content: str
    salience: float = Field(default=0.5, ge=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str | None = "benchmark"


class RecallQueryFixture(BaseModel):
    query: str
    expected_in_top_k: list[str] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=100)


class ConsolidationEpisodeFixture(BaseModel):
    session_id: str
    events: list[str]


class ConsolidationFixture(BaseModel):
    min_pattern_occurrences: int = Field(default=2, ge=2)
    episodes: list[ConsolidationEpisodeFixture] = Field(default_factory=list)


class BenchmarkDataset(BaseModel):
    name: str = "default"
    description: str = ""
    memories: list[MemoryFixture] = Field(default_factory=list)
    recall_queries: list[RecallQueryFixture] = Field(default_factory=list)
    consolidation: ConsolidationFixture | None = None


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_dataset_path(*, smoke: bool) -> Path:
    filename = "smoke.json" if smoke else "standard.json"
    return project_root() / "benchmarks" / "datasets" / filename


def load_dataset(path: Path) -> BenchmarkDataset:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return BenchmarkDataset.model_validate(payload)
