import asyncio
from pathlib import Path

import typer

app = typer.Typer(
    name="dendridb",
    help="DendriDB command-line interface.",
    no_args_is_help=True,
)

consolidate_app = typer.Typer(help="Run consolidation jobs.")
decay_app = typer.Typer(help="Run decay and forgetting jobs.")
benchmark_app = typer.Typer(help="Run performance and quality benchmarks.")
app.add_typer(consolidate_app, name="consolidate")
app.add_typer(decay_app, name="decay")
app.add_typer(benchmark_app, name="benchmark")


@app.command()
def version() -> None:
    """Print the installed DendriDB version."""
    from dendridb import __version__

    typer.echo(f"DendriDB {__version__}")


@consolidate_app.command("run")
def consolidate_run(
    namespace: str = typer.Option(..., "--namespace", "-n", help="Namespace to consolidate"),
    lookback_hours: int = typer.Option(168, "--lookback-hours", help="Episode replay window"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without writing changes"),
) -> None:
    """Replay recent episodes, merge duplicates, and promote repeated patterns."""
    from dendridb.api.schemas.consolidation import ConsolidationRunRequest
    from dendridb.core.database import get_session_factory
    from dendridb.services.consolidation import start_consolidation

    async def _run() -> None:
        session_factory = get_session_factory()
        async with session_factory() as session:
            job = await start_consolidation(
                session,
                ConsolidationRunRequest(
                    namespace=namespace,
                    lookback_hours=lookback_hours,
                    dry_run=dry_run,
                ),
                trigger="cli",
            )
            typer.echo(f"Consolidation job {job.id} completed with status {job.status}")
            typer.echo(job.stats)

    asyncio.run(_run())


@decay_app.command("run")
def decay_run(
    namespace: str = typer.Option(..., "--namespace", "-n", help="Namespace to decay"),
    half_life_hours: float | None = typer.Option(None, "--half-life-hours"),
    min_salience: float | None = typer.Option(None, "--min-salience"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Apply salience decay and archive low-value memories."""
    from dendridb.api.schemas.decay import DecayRunRequest
    from dendridb.core.database import get_session_factory
    from dendridb.services.decay import start_decay

    async def _run() -> None:
        session_factory = get_session_factory()
        async with session_factory() as session:
            job = await start_decay(
                session,
                DecayRunRequest(
                    namespace=namespace,
                    half_life_hours=half_life_hours,
                    min_salience=min_salience,
                    dry_run=dry_run,
                ),
                trigger="cli",
            )
            typer.echo(f"Decay job {job.id} completed with status {job.status}")
            typer.echo(job.stats)

    asyncio.run(_run())


@benchmark_app.command("run")
def benchmark_run(
    namespace: str = typer.Option("benchmark", "--namespace", "-n"),
    smoke: bool = typer.Option(False, "--smoke", help="Run the minimal CI smoke dataset"),
    dataset: Path | None = typer.Option(None, "--dataset", help="Path to a benchmark dataset JSON"),
    output_dir: Path | None = typer.Option(
        None, "--output-dir", help="Directory for JSON/Markdown reports"
    ),
    no_reports: bool = typer.Option(False, "--no-reports", help="Skip writing report files"),
) -> None:
    """Measure ingestion, recall, consolidation, and storage for a namespace."""
    from dendridb.benchmark.runner import run_benchmark_suite
    from dendridb.core.database import get_session_factory

    async def _run() -> None:
        session_factory = get_session_factory()
        async with session_factory() as session:
            result = await run_benchmark_suite(
                session,
                namespace=namespace,
                smoke=smoke,
                dataset_path=dataset,
                output_dir=output_dir,
                write_reports=not no_reports,
            )
        typer.echo(f"Benchmark {result.mode} {'passed' if result.passed else 'failed'}")
        if result.failures:
            for failure in result.failures:
                typer.echo(f"- {failure}", err=True)
            raise typer.Exit(code=1)

    asyncio.run(_run())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
