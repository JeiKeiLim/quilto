"""Base Typer application for Swealog CLI."""

from importlib.metadata import version

import typer

from swealog.cli.import_cmd import import_file


def _get_version() -> str:
    """Get swealog version from installed package metadata.

    Returns:
        Version string, or 'unknown' if package not installed.
    """
    try:
        return version("swealog")
    except Exception:
        return "unknown"


def version_callback(value: bool) -> None:
    """Print version and exit if --version flag is provided.

    Args:
        value: Whether --version flag was passed.
    """
    if value:
        print(f"swealog version {_get_version()}")
        raise typer.Exit()


app = typer.Typer(
    name="swealog",
    help="Fitness logging application powered by Quilto",
    no_args_is_help=True,
)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Swealog - AI-powered fitness logging."""


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
) -> None:
    """Start the Swealog API server.

    Runs uvicorn with the FastAPI application.

    Args:
        host: Host address to bind the server to.
        port: Port number to bind the server to.
        reload: Whether to enable auto-reload for development.
    """
    import uvicorn

    uvicorn.run(
        "swealog.api:app",
        host=host,
        port=port,
        reload=reload,
    )


# Register import command (name="import" since "import" is reserved keyword)
app.command(name="import")(import_file)
