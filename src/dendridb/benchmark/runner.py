"""Orchestrate benchmark scenarios and write reports."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.benchmark.dataset import (
    default_dataset_path,
    load_dataset,
    project_root,
)
from dendridb.benchmark.report import (
    BenchmarkSuiteResult,
    evaluate_thresholds,
    write_json_report,
    write_markdown_report,
)
from dendridb.benchmark.scenarios import (
    cleanup_namespace,
    run_consolidation_benchmark,
    run_ingestion_benchmark,
    run_recall_benchmark,
    run_storage_snapshot,
    seed_consolidation_episodes,
)
from dendridb.config import get_settings


async def run_benchmark_suite(
    session: AsyncSession,
    *,
    namespace: str = "benchmark",
    smoke: bool = False,
    dataset_path: Path | None = None,
    output_dir: Path | None = None,
    write_reports: bool = True,
) -> BenchmarkSuiteResult:
    settings = get_settings()
    path = dataset_path or default_dataset_path(smoke=smoke)
    dataset = load_dataset(path)
    mode = "smoke" if smoke else "full"
    thresholds = _thresholds_for_mode(smoke)

    await cleanup_namespace(session, namespace)
    ingestion = await run_ingestion_benchmark(session, namespace=namespace, dataset=dataset)
    await seed_consolidation_episodes(session, namespace=namespace, dataset=dataset)
    recall = await run_recall_benchmark(session, namespace=namespace, dataset=dataset)
    consolidation = await run_consolidation_benchmark(session, namespace=namespace, dataset=dataset)
    storage = await run_storage_snapshot(session, namespace=namespace)

    result = evaluate_thresholds(
        BenchmarkSuiteResult(
            mode=mode,
            namespace=namespace,
            dataset=path.name,
            environment=settings.environment,
            scenarios={
                "ingestion": ingestion,
                "recall": recall,
                "consolidation": consolidation,
                "storage": storage,
            },
            thresholds=thresholds,
        )
    )

    if write_reports:
        reports_dir = output_dir or (project_root() / "benchmarks" / "reports")
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        write_json_report(result, reports_dir / f"benchmark-{mode}-{timestamp}.json")
        write_markdown_report(result, reports_dir / f"benchmark-{mode}-{timestamp}.md")

    return result


def _thresholds_for_mode(smoke: bool) -> dict:
    if smoke:
        return {
            "min_recall_hit_rate": 1.0,
        }
    return {
        "min_recall_hit_rate": 0.8,
        "min_ingestion_records_per_second": 1.0,
    }
