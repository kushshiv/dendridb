import typer

app = typer.Typer(
    name="dendridb",
    help="DendriDB command-line interface.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Print the installed DendriDB version."""
    from dendridb import __version__

    typer.echo(f"DendriDB {__version__}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
