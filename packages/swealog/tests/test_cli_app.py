"""Tests for swealog.cli.app module."""

from swealog import __version__
from swealog.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_app_exists() -> None:
    """Test that the app instance is available."""
    assert app is not None


def test_version_flag() -> None:
    """Test --version displays version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "swealog version" in result.stdout
    assert __version__ in result.stdout


def test_short_version_flag() -> None:
    """Test -v displays version."""
    result = runner.invoke(app, ["-v"])
    assert result.exit_code == 0
    assert "swealog version" in result.stdout


def test_help_flag() -> None:
    """Test --help displays help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # Help text shows app name (lowercase) or description
    assert "swealog" in result.stdout.lower()


def test_no_args_shows_help() -> None:
    """Test that no arguments shows help (output shown)."""
    result = runner.invoke(app)
    # no_args_is_help=True shows help, and for rich panels the exit code may be 2
    # The important thing is that help content is shown
    assert "Usage" in result.stdout or "--help" in result.stdout


def test_app_can_add_command() -> None:
    """Test that commands can be added to a Typer app (extensibility).

    Uses a fresh app instance to avoid polluting shared state.
    """
    import typer

    # Create a fresh main app for isolation
    main_app = typer.Typer(name="test-main", no_args_is_help=True)

    @main_app.callback()
    def main_callback() -> None:  # pyright: ignore[reportUnusedFunction]
        """Test main app."""

    sub_app = typer.Typer()

    @sub_app.command()
    def test_cmd_example() -> None:  # pyright: ignore[reportUnusedFunction]
        """A test command."""
        print("test output")

    # Verify add_typer works on fresh app
    main_app.add_typer(sub_app, name="testgroup")

    result = runner.invoke(main_app, ["testgroup", "test-cmd-example"])
    assert result.exit_code == 0
    assert "test output" in result.stdout


def test_app_command_decorator() -> None:
    """Test that @app.command() decorator works (extensibility)."""
    # Create a fresh app with a single command
    import typer

    test_app = typer.Typer()

    @test_app.command()
    def mycommand() -> None:  # pyright: ignore[reportUnusedFunction]
        """A decorated command."""
        print("decorated output")

    test_runner = CliRunner()
    # When app has single command, it becomes the default
    result = test_runner.invoke(test_app)
    assert result.exit_code == 0
    assert "decorated output" in result.stdout
