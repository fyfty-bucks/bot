"""Tests for code validator."""

import textwrap
from pathlib import Path

from src.utils.lint import (
    analyze_py, analyze_md, parse_gitignore, is_ignored,
    format_report, LintResult, FileReport,
)


def test_analyze_py_clean(tmp_path: Path) -> None:
    """Clean Python file passes all checks."""
    f = tmp_path / "clean.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        def greet(name: str) -> str:
            return f"hello {name}"
    '''))
    report = analyze_py(f)
    assert report.passed


def test_analyze_py_too_many_lines(tmp_path: Path) -> None:
    """File over 200 lines fails."""
    f = tmp_path / "big.py"
    lines = ['"""Module doc."""\n'] + ["x = 1\n"] * 201
    f.write_text("".join(lines))
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "lines" in rules


def test_analyze_py_no_docstring(tmp_path: Path) -> None:
    """File without module docstring fails."""
    f = tmp_path / "nodoc.py"
    f.write_text("x = 1\n")
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "docstring" in rules


def test_analyze_py_missing_type_hint(tmp_path: Path) -> None:
    """Public function without return type fails type_hints check."""
    f = tmp_path / "notype.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        def greet(name):
            return f"hello {name}"
    '''))
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "type_hints" in rules


def test_analyze_py_private_no_type_hint_ok(tmp_path: Path) -> None:
    """Private function without type hint is fine."""
    f = tmp_path / "private.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        def _helper(x):
            return x + 1
    '''))
    report = analyze_py(f)
    assert report.passed


def test_analyze_py_secret_detected(tmp_path: Path) -> None:
    """Secret pattern in code triggers failure."""
    f = tmp_path / "leak.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        API_KEY = "sk-abc123def456ghi789jkl012mno345"
    '''))
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "secret" in rules


def test_analyze_md_clean(tmp_path: Path) -> None:
    """Short markdown passes."""
    f = tmp_path / "doc.md"
    f.write_text("# Title\n\nContent\n")
    report = analyze_md(f)
    assert report.passed


def test_analyze_md_too_long(tmp_path: Path) -> None:
    """Markdown over 150 lines fails."""
    f = tmp_path / "long.md"
    f.write_text("\n".join(["line"] * 160))
    report = analyze_md(f)
    assert not report.passed


def test_parse_gitignore(tmp_path: Path) -> None:
    """Gitignore patterns parsed correctly."""
    gi = tmp_path / ".gitignore"
    gi.write_text("secrets/\n__pycache__/\n# comment\n!keep\n*.pyc\n")
    patterns = parse_gitignore(tmp_path)
    assert "secrets/" in patterns or "secrets" in patterns
    assert "__pycache__/" in patterns or "__pycache__" in patterns
    assert "*.pyc" in patterns
    assert "!keep" not in patterns


def test_is_ignored(tmp_path: Path) -> None:
    """Ignored paths detected."""
    patterns = ["secrets/", "__pycache__/", "*.pyc"]
    secret = tmp_path / "secrets" / "key.env"
    secret.parent.mkdir()
    secret.touch()
    assert is_ignored(secret, tmp_path, patterns)

    src = tmp_path / "src" / "main.py"
    src.parent.mkdir()
    src.touch()
    assert not is_ignored(src, tmp_path, patterns)


def test_format_report_ok() -> None:
    """Clean report shows RESULT: OK."""
    r = FileReport(Path("a.py"), 10, [
        LintResult("a.py", "lines", 10, 200, True),
    ])
    output = format_report([r])
    assert "RESULT: OK" in output


def test_format_report_fail() -> None:
    """Failed report shows RESULT: FAIL with details."""
    r = FileReport(Path("a.py"), 250, [
        LintResult("a.py", "lines", 250, 200, False),
    ])
    output = format_report([r])
    assert "RESULT: FAIL" in output
    assert "lines=250" in output


def test_test_file_gets_relaxed_limits(tmp_path: Path) -> None:
    """Test files get 300 line limit, not 200."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    f = tests_dir / "test_something.py"
    lines = ['"""Test module."""\n'] + ["def test_x(): pass\n"] * 250
    f.write_text("".join(lines))
    report = analyze_py(f)
    line_check = [r for r in report.results if r.rule == "lines"][0]
    assert line_check.limit == 300
    assert line_check.passed
