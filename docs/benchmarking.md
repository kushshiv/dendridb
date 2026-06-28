# Benchmarking Guide

DendriDB includes a benchmark suite for measuring ingestion throughput, recall latency, recall quality, consolidation runtime, and storage growth.

## Quick start

With PostgreSQL running and migrations applied:

```bash
make docker-up
make migrate
make benchmark          # smoke dataset (CI-friendly)
make benchmark-full     # standard dataset with reports
```

Reports are written to `benchmarks/reports/` as JSON and Markdown files.

## CLI

```bash
dendridb benchmark run --smoke
dendridb benchmark run --dataset benchmarks/datasets/standard.json
dendridb benchmark run --namespace team-a --output-dir benchmarks/reports
```

Use `--no-reports` to print pass/fail only without writing files.

## Scenarios

| Scenario | Measures |
|----------|----------|
| Ingestion | Memory create throughput and per-record latency |
| Recall | Query latency and quality hit rate against expected keywords |
| Consolidation | Job duration and promotion/merge stats |
| Storage | Record counts after the benchmark run |

## Datasets

Datasets live in `benchmarks/datasets/`:

- `smoke.json` — minimal deterministic set used in CI
- `standard.json` — default local benchmark with more memories and queries

Each dataset defines:

- `memories` — records to ingest
- `recall_queries` — queries with optional `expected_in_top_k` substrings
- `consolidation` — repeated episode events for promotion checks

## Quality thresholds

Smoke mode requires 100% recall quality hits. Full mode requires at least 80% recall quality hits and minimum ingestion throughput of 1 record/sec.

Threshold failures mark the benchmark run as failed and exit with a non-zero code.

## CI smoke check

Integration tests include `tests/integration/test_benchmark_smoke.py`, which runs the smoke suite in-process against PostgreSQL. This guards against silent recall regressions without relying on flaky timing assertions.

See also [hardening.md](hardening.md) for operational readiness guidance.
