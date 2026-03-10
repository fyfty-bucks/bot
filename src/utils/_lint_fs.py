"""Lint filesystem: gitignore-aware file collection."""

from pathlib import Path

import pathspec


def load_gitignore(root: Path) -> pathspec.PathSpec:
    """Load root .gitignore as a pathspec.PathSpec."""
    gi = root / ".gitignore"
    if not gi.exists():
        return pathspec.PathSpec.from_lines("gitignore", [])
    return pathspec.PathSpec.from_lines(
        "gitignore",
        gi.read_text().splitlines(),
    )


def is_ignored(path: Path, root: Path, spec: pathspec.PathSpec) -> bool:
    """Check if path matches any .gitignore pattern."""
    rel = str(path.relative_to(root))
    return spec.match_file(rel)


def collect_files(target: Path, root: Path | None = None) -> list[Path]:
    """Collect lintable files under target, respecting .gitignore from root."""
    if root is None:
        root = target
    spec = load_gitignore(root)
    files = []
    for p in sorted(target.rglob("*")):
        if not p.is_file():
            continue
        if is_ignored(p, root, spec):
            continue
        if p.suffix in (".py", ".md", ".mdc"):
            files.append(p)
    return files
