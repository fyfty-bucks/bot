"""Tests for lint integration: lint_path, format_report, gitignore."""

from pathlib import Path

from src.utils.lint import (
    lint_path, load_gitignore, is_ignored,
    format_report, LintResult, FileReport,
)


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


def test_is_ignored_via_pathspec(tmp_path: Path) -> None:
    """is_ignored detects matches via pathspec.PathSpec."""
    gi = tmp_path / ".gitignore"
    gi.write_text("secrets/\n__pycache__/\n*.pyc\n")
    spec = load_gitignore(tmp_path)

    secret = tmp_path / "secrets" / "key.env"
    secret.parent.mkdir()
    secret.touch()
    assert is_ignored(secret, tmp_path, spec)

    src = tmp_path / "src" / "main.py"
    src.parent.mkdir()
    src.touch()
    assert not is_ignored(src, tmp_path, spec)


def test_load_gitignore_returns_pathspec(tmp_path: Path) -> None:
    """load_gitignore returns a pathspec.PathSpec object."""
    import pathspec as ps
    gi = tmp_path / ".gitignore"
    gi.write_text("secrets/\n__pycache__/\n*.pyc\n")
    spec = load_gitignore(tmp_path)
    assert isinstance(spec, ps.PathSpec)


def test_load_gitignore_matches_patterns(tmp_path: Path) -> None:
    """PathSpec correctly matches gitignore patterns."""
    gi = tmp_path / ".gitignore"
    gi.write_text("secrets/\n__pycache__/\n*.pyc\n# comment\n")
    spec = load_gitignore(tmp_path)
    assert spec.match_file("secrets/key.env")
    assert spec.match_file("__pycache__/foo.pyc")
    assert spec.match_file("some.pyc")
    assert not spec.match_file("src/main.py")


def test_load_gitignore_handles_negation(tmp_path: Path) -> None:
    """PathSpec handles negation patterns (!) correctly."""
    gi = tmp_path / ".gitignore"
    gi.write_text("*.log\n!important.log\n")
    spec = load_gitignore(tmp_path)
    assert spec.match_file("debug.log")
    assert not spec.match_file("important.log")


def test_load_gitignore_missing_file(tmp_path: Path) -> None:
    """Missing .gitignore returns empty spec that matches nothing."""
    spec = load_gitignore(tmp_path)
    assert not spec.match_file("anything.py")
    assert not spec.match_file("secrets/key.env")


def test_load_gitignore_globstar(tmp_path: Path) -> None:
    """PathSpec handles ** globstar patterns."""
    gi = tmp_path / ".gitignore"
    gi.write_text("**/build/\n**/*.tmp\n")
    spec = load_gitignore(tmp_path)
    assert spec.match_file("project/build/output.js")
    assert spec.match_file("deep/nested/file.tmp")
    assert not spec.match_file("src/main.py")


def test_lint_path_single_py_file(tmp_path: Path) -> None:
    """lint_path on single .py file returns one report."""
    f = tmp_path / "mod.py"
    f.write_text('"""Module doc."""\n\ndef greet() -> str:\n    return "hi"\n')
    reports = lint_path(f)
    assert len(reports) == 1
    assert reports[0].passed


def test_lint_path_single_md_file(tmp_path: Path) -> None:
    """lint_path on single .md file returns one report."""
    f = tmp_path / "doc.md"
    f.write_text("# Title\n\nContent\n")
    reports = lint_path(f)
    assert len(reports) == 1
    assert reports[0].passed


def test_lint_path_skips_non_lintable(tmp_path: Path) -> None:
    """lint_path ignores .txt, .json, and other non-lintable files."""
    (tmp_path / "data.json").write_text("{}")
    (tmp_path / "notes.txt").write_text("hello")
    (tmp_path / "mod.py").write_text('"""Doc."""\n')
    reports = lint_path(tmp_path)
    assert len(reports) == 1
    assert reports[0].path.name == "mod.py"


def test_lint_path_directory(tmp_path: Path) -> None:
    """lint_path on directory collects all lintable files."""
    (tmp_path / "a.py").write_text('"""Doc."""\n')
    (tmp_path / "b.md").write_text("# B\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.py").write_text('"""Doc."""\n')
    reports = lint_path(tmp_path)
    names = {r.path.name for r in reports}
    assert names == {"a.py", "b.md", "c.py"}


def test_lint_path_unknown_extension(tmp_path: Path) -> None:
    """lint_path on a single non-lintable file returns empty list."""
    f = tmp_path / "data.json"
    f.write_text("{}")
    reports = lint_path(f)
    assert reports == []
