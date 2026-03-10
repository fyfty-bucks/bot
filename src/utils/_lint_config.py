"""Lint limits loader — single source of truth in pyproject.toml."""

import tomllib
from pathlib import Path

_DEFAULTS = {
    "src": {
        "lines": 200, "functions": 7, "classes": 3,
        "func_lines": 50, "imports": 15,
    },
    "tests": {
        "lines": 300, "functions": 25, "classes": 5,
        "func_lines": 50, "imports": 15,
    },
    "docs": {"lines": 150},
}


def _find_pyproject() -> Path:
    """Locate pyproject.toml from project root (3 levels up from this file)."""
    return Path(__file__).resolve().parent.parent.parent / "pyproject.toml"


def load_limits() -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    """Load lint limits: pyproject.toml [tool.agent-lint] > defaults."""
    path = _find_pyproject()
    if not path.exists():
        return {**_DEFAULTS["src"]}, {**_DEFAULTS["tests"]}, {**_DEFAULTS["docs"]}

    with open(path, "rb") as f:
        config = tomllib.load(f)

    lint = config.get("tool", {}).get("agent-lint", {})
    return (
        {**_DEFAULTS["src"], **lint.get("src", {})},
        {**_DEFAULTS["tests"], **lint.get("tests", {})},
        {**_DEFAULTS["docs"], **lint.get("docs", {})},
    )


PY_LIMITS, TEST_LIMITS, MD_LIMITS = load_limits()
