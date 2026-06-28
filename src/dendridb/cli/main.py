import asyncio

import typer

app = typer.Typer(
    name="dendridb",
    help="DendriDB command-line interface.",
    no_args_is_help=True,
)

consolidate_app = typer.Typer(help="Run consolidation jobs.")
app.add_typer(consolidate_app, name="consolidate")


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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
