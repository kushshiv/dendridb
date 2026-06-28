import pytest

from dendridb.benchmark.dataset import load_dataset, project_root
from dendridb.benchmark.report import (
    BenchmarkSuiteResult,
    evaluate_thresholds,
    render_markdown_report,
)
from dendridb.benchmark.timing import summarize_seconds, to_milliseconds


@pytest.mark.unit
def test_summarize_seconds_empty():
    summary = summarize_seconds([])
    assert summary["count"] == 0.0
    assert summary["mean_seconds"] == 0.0


@pytest.mark.unit
def test_summarize_seconds_computes_percentiles():
    summary = summarize_seconds([0.01, 0.02, 0.03, 0.04, 0.05])
    assert summary["count"] == 5.0
    assert summary["min_seconds"] == pytest.approx(0.01)
    assert summary["max_seconds"] == pytest.approx(0.05)
    assert to_milliseconds(summary["p50_seconds"]) == pytest.approx(20.0)


@pytest.mark.unit
def test_load_smoke_dataset():
    dataset = load_dataset(project_root() / "benchmarks" / "datasets" / "smoke.json")
    assert dataset.name == "smoke"
    assert len(dataset.memories) >= 2
    assert len(dataset.recall_queries) >= 1


@pytest.mark.unit
def test_evaluate_thresholds_flags_recall_regression():
    result = BenchmarkSuiteResult(
        mode="smoke",
        namespace="bench",
        dataset="smoke.json",
        environment="test",
        scenarios={"recall": {"quality_queries": 2, "quality_hit_rate": 0.5}},
        thresholds={"min_recall_hit_rate": 1.0},
    )
    evaluated = evaluate_thresholds(result)
    assert evaluated.passed is False
    assert evaluated.failures


@pytest.mark.unit
def test_render_markdown_report_includes_status():
    result = BenchmarkSuiteResult(
        mode="smoke",
        namespace="bench",
        dataset="smoke.json",
        environment="test",
        scenarios={"ingestion": {"records_created": 3}},
        passed=True,
    )
    markdown = render_markdown_report(result)
    assert "PASS" in markdown
    assert "Ingestion" in markdown
