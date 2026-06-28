"""Benchmark report models and writers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from dendridb.benchmark.timing import utc_now_iso


class BenchmarkSuiteResult(BaseModel):
    generated_at: str = Field(default_factory=utc_now_iso)
    mode: str
    namespace: str
    dataset: str
    environment: str
    scenarios: dict[str, Any]
    thresholds: dict[str, Any] = Field(default_factory=dict)
    passed: bool = True
    failures: list[str] = Field(default_factory=list)


def evaluate_thresholds(result: BenchmarkSuiteResult) -> BenchmarkSuiteResult:
    failures: list[str] = []
    recall = result.scenarios.get("recall", {})
    if recall and recall.get("quality_queries", 0) > 0:
        min_hit_rate = result.thresholds.get("min_recall_hit_rate", 1.0)
        hit_rate = recall.get("quality_hit_rate", 0.0)
        if hit_rate < min_hit_rate:
            failures.append(f"recall quality hit rate {hit_rate} below threshold {min_hit_rate}")

    consolidation = result.scenarios.get("consolidation", {})
    if (
        consolidation
        and not consolidation.get("skipped")
        and consolidation.get("job_status") != "completed"
    ):
        failures.append(f"consolidation job status {consolidation.get('job_status')} != completed")

    ingestion = result.scenarios.get("ingestion", {})
    min_throughput = result.thresholds.get("min_ingestion_records_per_second")
    if min_throughput is not None:
        throughput = ingestion.get("throughput_records_per_second", 0.0)
        if throughput < min_throughput:
            failures.append(f"ingestion throughput {throughput} below threshold {min_throughput}")

    result.failures = failures
    result.passed = not failures
    return result


def write_json_report(result: BenchmarkSuiteResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.model_dump(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def render_markdown_report(result: BenchmarkSuiteResult) -> str:
    lines = [
        "# DendriDB Benchmark Report",
        "",
        f"- Generated: {result.generated_at}",
        f"- Mode: `{result.mode}`",
        f"- Namespace: `{result.namespace}`",
        f"- Dataset: `{result.dataset}`",
        f"- Environment: `{result.environment}`",
        f"- Overall: **{'PASS' if result.passed else 'FAIL'}**",
        "",
    ]

    if result.failures:
        lines.extend(["## Failures", ""])
        for failure in result.failures:
            lines.append(f"- {failure}")
        lines.append("")

    for name, payload in result.scenarios.items():
        lines.extend([f"## {name.replace('_', ' ').title()}", ""])
        lines.extend(_render_scenario_lines(payload))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_scenario_lines(payload: Any, indent: int = 0) -> list[str]:
    prefix = "  " * indent
    lines: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}- **{key}**:")
                lines.extend(_render_scenario_lines(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}- **{key}**: {json.dumps(value)}")
            else:
                lines.append(f"{prefix}- **{key}**: {value}")
    else:
        lines.append(f"{prefix}- {payload}")
    return lines


def write_markdown_report(result: BenchmarkSuiteResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown_report(result), encoding="utf-8")
