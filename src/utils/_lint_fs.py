"""Lint filesystem: .gitignore parsing and file collection."""

from pathlib import Path
from fnmatch import fnmatch


def parse_gitignore(root: Path) -> list[str]:
    """Read .gitignore patterns from project root."""
    gi = root / ".gitignore"
    if not gi.exists():
        return []
    patterns = []
    for line in gi.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("!"):
            patterns.append(line)
    return patterns


def is_ignored(path: Path, root: Path, patterns: list[str]) -> bool:
    """Check if path matches any .gitignore pattern."""
    rel = str(path.relative_to(root))
    parts = path.relative_to(root).parts
    for pat in patterns:
        pat_clean = pat.rstrip("/")
        if fnmatch(rel, pat_clean) or fnmatch(rel, pat_clean + "/**"):
            return True
        if any(fnmatch(p, pat_clean) for p in parts):
            return True
        for i in range(len(parts)):
            sub = "/".join(parts[:i+1])
            if fnmatch(sub, pat_clean) or fnmatch(sub + "/", pat):
                return True
    return False


def collect_files(root: Path) -> list[Path]:
    """Collect all lintable files, respecting .gitignore."""
    patterns = parse_gitignore(root)
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if is_ignored(p, root, patterns):
            continue
        if p.suffix in (".py", ".md", ".mdc"):
            files.append(p)
    return files
