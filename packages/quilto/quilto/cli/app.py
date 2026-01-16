"""Base Typer application for Quilto CLI."""

from importlib.metadata import version

import typer


def _get_version() -> str:
    """Get quilto version from installed package metadata.

    Returns:
        Version string, or 'unknown' if package not installed.
    """
    try:
        return version("quilto")
    except Exception:
        return "unknown"


def version_callback(value: bool) -> None:
    """Print version and exit if --version flag is provided.

    Args:
        value: Whether --version flag was passed.
    """
    if value:
        print(f"quilto version {_get_version()}")
        raise typer.Exit()


app = typer.Typer(
    name="quilto",
    help="Domain-agnostic agent framework for note processing",
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
    """Quilto - Domain-agnostic agent framework."""
