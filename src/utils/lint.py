"""Code and docs validator. Respects .gitignore, checks limits + secrets."""

from pathlib import Path

from src.utils._lint_core import (
    LintResult, FileReport,
    analyze_py, analyze_md,
)
from src.utils._lint_fs import parse_gitignore, is_ignored, collect_files
from src.utils._lint_report import format_report


def lint_path(target: Path, root: Path | None = None) -> list[FileReport]:
    """Lint file or directory. Respects .gitignore from root."""
    if root is None:
        root = target if target.is_dir() else target.parent

    if target.is_file():
        if target.suffix == ".py":
            return [analyze_py(target)]
        if target.suffix in (".md", ".mdc"):
            return [analyze_md(target)]
        return []

    patterns = parse_gitignore(root)
    reports: list[FileReport] = []
    for p in sorted(target.rglob("*")):
        if not p.is_file():
            continue
        if is_ignored(p, root, patterns):
            continue
        if p.suffix == ".py":
            reports.append(analyze_py(p))
        elif p.suffix in (".md", ".mdc"):
            reports.append(analyze_md(p))
    return reports


__all__ = [
    "LintResult", "FileReport",
    "analyze_py", "analyze_md",
    "parse_gitignore", "is_ignored", "collect_files",
    "format_report", "lint_path",
]
