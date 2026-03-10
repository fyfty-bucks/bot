"""Tests for CLI command routing and discovery."""

from io import StringIO
from unittest.mock import patch

from src.cli import main


def _run_main(*args: str) -> tuple[int, str]:
    """Run main() with patched sys.argv, return (exit_code, stdout)."""
    argv = ["agent"] + list(args)
    out = StringIO()
    with patch("sys.argv", argv), patch("sys.stdout", out):
        code = main()
    return code, out.getvalue()


def test_no_args_shows_help_with_commands() -> None:
    """No arguments prints help (exit 2) listing all discovered commands."""
    code, output = _run_main()
    assert code == 2
    assert "usage" in output.lower()
    assert "lint" in output
    assert "tests" in output


def test_info_command_runs() -> None:
    """info command executes and returns 0."""
    code, output = _run_main("info")
    assert code == 0
    assert "50bucks" in output
